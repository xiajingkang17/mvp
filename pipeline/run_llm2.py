from __future__ import annotations

import argparse
import json
import re
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from components.common.inline_math import (
    has_latex_tokens_outside_inline_math,
    has_unbalanced_inline_math_delimiters,
    split_inline_math_segments,
)
from components.physics.specs import PHYSICS_OBJECT_PARAM_SPECS
from pipeline.config import load_enums
from pipeline.env import load_dotenv
from pipeline.json_utils import load_json_from_llm
from pipeline.llm.types import ChatMessage
from pipeline.llm.zhipu import chat_completion
from pipeline.llm_continuation import continue_json_output
from pipeline.prompting import load_prompt
from schema.composite_graph_models import CompositeGraph
from llm_constraints.constraints_spec import validate_constraint


_CJK_RE = re.compile(r"[\u3400-\u9fff]")
_LATEX_CMD_RE = re.compile(r"\\[a-zA-Z]+")
_LATEX_TOKEN_RE = re.compile(r"\\[a-zA-Z]+(?:\{[^{}]*\})?")
_TOP_LEVEL_OBJECT_TYPES = ("TextBlock", "BulletPanel", "Formula", "CompositeObject")
_MOVABLE_PART_TYPES = {"Block", "Cart", "Weight", "SemicircleCart", "QuarterCart"}
_CURVED_PART_TYPES = {"ArcTrack", "SemicircleGroove", "QuarterCircleGroove", "CircularGroove"}
_DYNAMIC_SCENE_KEYWORDS = (
    "动画",
    "动图",
    "运动过程",
    "滑动过程",
    "连续运动",
    "下滑",
    "碰撞",
    "轨迹",
    "motion",
    "animate",
    "slid",
    "slide",
    "collision",
)

_MECHANICS_TYPES = {
    "InclinedPlaneGroup",
    "Wall",
    "Block",
    "Cart",
    "Weight",
    "Pulley",
    "FixedPulley",
    "MovablePulley",
    "Rope",
    "Spring",
    "Rod",
    "Hinge",
    "CircularGroove",
    "ArcTrack",
    "SemicircleGroove",
    "QuarterCircleGroove",
    "SemicircleCart",
    "QuarterCart",
    "SpringScale",
}
_ELECTRICITY_TYPES = {"Resistor", "Battery", "Bulb", "Switch", "Capacitor"}
_ELECTROMAG_TYPES = {
    "EMBattery",
    "EMSwitch",
    "Ammeter",
    "Voltmeter",
    "LightBulb",
    "EMCapacitor",
    "Rheostat",
    "Potentiometer",
    "Inductor",
    "LED",
}

_COMPONENT_LABELS = {
    "InclinedPlaneGroup": "斜面+滑块整体",
    "Wall": "墙面/挡板",
    "Block": "方块/物块",
    "Cart": "小车",
    "Weight": "重物",
    "Pulley": "滑轮",
    "FixedPulley": "定滑轮",
    "MovablePulley": "动滑轮",
    "Rope": "绳子",
    "Spring": "弹簧",
    "Rod": "细杆/轨道段",
    "Hinge": "铰点",
    "CircularGroove": "圆形凹槽轨道",
    "SemicircleGroove": "半圆凹槽轨道",
    "QuarterCircleGroove": "四分之一圆凹槽",
    "SemicircleCart": "半圆小车",
    "QuarterCart": "四分之一圆小车",
    "SpringScale": "弹簧秤",
    "Resistor": "电阻",
    "Battery": "电池",
    "Bulb": "灯泡",
    "Switch": "开关",
    "Capacitor": "电容",
    "EMBattery": "电磁风格电池",
    "EMSwitch": "电磁风格开关",
    "Ammeter": "电流表",
    "Voltmeter": "电压表",
    "LightBulb": "小灯泡（电磁风格）",
    "EMCapacitor": "电磁风格电容",
    "Rheostat": "滑动变阻器",
    "Potentiometer": "电位器",
    "Inductor": "电感线圈",
    "LED": "发光二极管",
}

_COMPONENT_PURPOSES = {
    "InclinedPlaneGroup": "快速构建“斜面+物块”题意主图。",
    "Block": "表示受力/运动主体物块。",
    "Rope": "表示拉力路径或连接关系。",
    "Spring": "表示弹簧储能与压缩/伸长。",
    "Rod": "表示水平轨道、细杆或参考线。",
    "Pulley": "表示一般滑轮模型。",
    "FixedPulley": "表示定滑轮改变力方向。",
    "MovablePulley": "表示动滑轮省力结构。",
    "Resistor": "表示电阻元件。",
    "Battery": "表示电源。",
    "Switch": "表示开关状态。",
    "Capacitor": "表示电容储能。",
    "Ammeter": "表示电流测量点。",
    "Voltmeter": "表示电压测量点。",
    "Rheostat": "表示可变电阻调节。",
    "Inductor": "表示电感线圈与磁场相关现象。",
    "LED": "表示单向导通与发光元件。",
}

_DOMAIN_KEYWORDS = {
    "mechanics": [
        "力学",
        "斜面",
        "滑块",
        "物块",
        "摩擦",
        "弹簧",
        "碰撞",
        "动能",
        "势能",
        "机械能",
        "速度",
        "加速度",
        "滑轮",
        "绳",
    ],
    "electricity": [
        "电学",
        "电路",
        "电阻",
        "电容",
        "电池",
        "开关",
        "灯泡",
        "串联",
        "并联",
        "欧姆",
        "电流",
        "电压",
    ],
    "electromagnetism": [
        "电磁",
        "磁场",
        "电感",
        "线圈",
        "感应",
        "安培表",
        "电流表",
        "电压表",
        "伏特表",
        "滑动变阻器",
        "电位器",
        "led",
    ],
}

_PHYSICS_FAMILY_KEYWORDS = [
    "物理",
    "力学",
    "电学",
    "电磁",
    "受力",
    "运动",
    "速度",
    "加速度",
    "电流",
    "电压",
    "magnetic",
    "mechanics",
    "electricity",
    "electromagnetism",
    "physics",
]


class DraftObjectSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    type: str = Field(min_length=1)
    params: dict[str, Any] = Field(default_factory=dict)
    style: dict[str, Any] = Field(default_factory=dict)
    priority: int = Field(default=2, ge=1, le=9)
    anchor: str | None = None
    z_index: int | None = None


class DraftSceneSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    intent: str | None = None
    objects: list[DraftObjectSpec] = Field(default_factory=list)
    notes: str | None = None
    goal: str | None = None
    modules: list[str] = Field(default_factory=list)
    roles: dict[str, str] = Field(default_factory=dict)
    new_symbols: list[str] = Field(default_factory=list)
    is_check_scene: bool = False


class DraftCognitiveBudget(BaseModel):
    model_config = ConfigDict(extra="forbid")

    max_visible_objects: int = Field(default=4, ge=1, le=9)
    max_new_formula: int = Field(default=4, ge=1, le=9)
    max_new_symbols: int = Field(default=3, ge=0, le=20)
    max_text_chars: int = Field(default=60, ge=8, le=200)


class DraftPedagogyPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    difficulty: Literal["simple", "medium", "hard"] = "medium"
    need_single_goal: bool = False
    need_check_scene: bool = False
    check_types: list[Literal["unit", "boundary", "feasibility", "reasonableness"]] = Field(default_factory=list)
    cognitive_budget: DraftCognitiveBudget = Field(default_factory=DraftCognitiveBudget)
    module_order: list[str] = Field(default_factory=list)


class SceneDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scenes: list[DraftSceneSpec] = Field(default_factory=list)
    pedagogy_plan: DraftPedagogyPlan | None = None

    @model_validator(mode="after")
    def _validate_unique_scene_ids(self) -> "SceneDraft":
        seen: set[str] = set()
        for scene in self.scenes:
            if scene.id in seen:
                raise ValueError(f"Duplicate scene id: {scene.id}")
            seen.add(scene.id)
        return self


def _write_continuation_chunks(case_dir: Path, stem: str, chunks: list[str]) -> None:
    for idx, chunk in enumerate(chunks, start=1):
        (case_dir / f"{stem}_{idx}.txt").write_text(chunk.strip() + "\n", encoding="utf-8")


def _contains_cjk(text: str) -> bool:
    return bool(_CJK_RE.search(text))


def _scene_requires_motion(scene: DraftSceneSpec) -> bool:
    chunks: list[str] = []
    for value in (scene.intent, scene.goal, scene.notes):
        if isinstance(value, str) and value.strip():
            chunks.append(value.strip())
    chunks.extend([str(x).strip() for x in scene.modules if str(x).strip()])
    text = " ".join(chunks).lower()
    if not text:
        return False
    return any(keyword in text for keyword in _DYNAMIC_SCENE_KEYWORDS)


def _physics_param_catalog() -> dict[str, list[str]]:
    return {k: list(v) for k, v in sorted(PHYSICS_OBJECT_PARAM_SPECS.items())}


@lru_cache(maxsize=1)
def _load_llm_constraints_assets() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    base = Path("llm_constraints")
    constraints = json.loads((base / "specs" / "constraints_whitelist.json").read_text(encoding="utf-8"))
    anchors = json.loads((base / "specs" / "anchors_dictionary.json").read_text(encoding="utf-8"))
    catalog = json.loads((base / "specs" / "components_catalog.json").read_text(encoding="utf-8"))
    return constraints, anchors, catalog


@lru_cache(maxsize=1)
def _load_protocol_docs() -> dict[str, str]:
    base = Path("llm_constraints")
    names = [
        "protocols/index.md",
        "protocols/core.md",
        "protocols/assembly.md",
        "protocols/motion.md",
        "protocols/validation.md",
    ]
    docs: dict[str, str] = {}
    for name in names:
        path = base / name
        if path.exists():
            docs[name] = path.read_text(encoding="utf-8").strip()
    return docs


def _build_protocol_bundle_for_prompt(domains: list[str]) -> dict[str, Any]:
    docs = _load_protocol_docs()
    domain_set = set(domains)
    selected_order = [
        "protocols/index.md",
        "protocols/core.md",
        "protocols/assembly.md",
        "protocols/validation.md",
    ]
    if "mechanics" in domain_set or not domain_set:
        selected_order.append("protocols/motion.md")
    selected = {name: docs[name] for name in selected_order if name in docs}
    return {"files": list(selected.keys()), "docs": selected}


def _build_constraint_prompt_bundle(
    *,
    part_types: list[str],
    domains: list[str],
) -> dict[str, Any]:
    constraints_raw, anchors_raw, _ = _load_llm_constraints_assets()
    constraints_map = constraints_raw.get("constraints", {}) if isinstance(constraints_raw, dict) else {}
    components_map = anchors_raw.get("components", {}) if isinstance(anchors_raw, dict) else {}

    mechanics_mode = "mechanics" in set(domains)
    if mechanics_mode:
        allowed_constraints = sorted(constraints_map.keys())
    else:
        allowed_constraints = []

    anchors_subset: dict[str, Any] = {}
    for part_type in part_types:
        entry = components_map.get(part_type)
        if not isinstance(entry, dict):
            continue
        anchors = entry.get("anchors", [])
        anchors_subset[part_type] = {"anchors": list(anchors) if isinstance(anchors, list) else []}

    constraint_subset = {key: constraints_map[key] for key in allowed_constraints if key in constraints_map}
    return {
        "allowed_constraint_types": allowed_constraints,
        "constraints_whitelist": constraint_subset,
        "anchors_dictionary": anchors_subset,
    }


def _build_components_catalog_for_prompt(part_types: list[str], domains: list[str]) -> dict[str, Any]:
    _, _, catalog_raw = _load_llm_constraints_assets()
    components = catalog_raw.get("components", {}) if isinstance(catalog_raw, dict) else {}
    domain_set = set(domains)
    selected: dict[str, Any] = {}
    for comp_type in part_types:
        item = components.get(comp_type)
        if not isinstance(item, dict):
            continue
        item_domain = str(item.get("domain", "")).strip().lower()
        if item_domain and domain_set and item_domain not in domain_set:
            continue
        selected[comp_type] = item
    return selected


def _constraints_for_prompt_display(constraints_whitelist: dict[str, Any]) -> dict[str, Any]:
    rendered = json.loads(json.dumps(constraints_whitelist, ensure_ascii=False))
    if not isinstance(rendered, dict):
        return {}
    for _, item in rendered.items():
        if isinstance(item, dict):
            if "args" in item and "arg_specs" not in item:
                item["arg_specs"] = item.pop("args")
            elif "params" in item and "arg_specs" not in item:
                item["arg_specs"] = item.pop("params")
    return rendered


def _teaching_plan_context_text(teaching_plan: dict[str, Any] | None) -> str:
    if not isinstance(teaching_plan, dict):
        return ""
    parts: list[str] = []
    explanation_full = teaching_plan.get("explanation_full")
    if isinstance(explanation_full, str) and explanation_full.strip():
        parts.append(explanation_full.strip())
    sub_questions = teaching_plan.get("sub_questions")
    if isinstance(sub_questions, list):
        for item in sub_questions:
            if not isinstance(item, dict):
                continue
            for key in ("question", "goal", "transition"):
                value = item.get(key)
                if isinstance(value, str) and value.strip():
                    parts.append(value.strip())
    return "\n".join(parts)


def _infer_domains(problem: str, teaching_context: str) -> list[str]:
    text = f"{problem}\n{teaching_context}".lower()
    scores: dict[str, int] = {}
    for domain, keywords in _DOMAIN_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw and kw.lower() in text)
        scores[domain] = score

    hit_domains = [d for d, s in scores.items() if s > 0]
    if hit_domains:
        return hit_domains
    return ["mechanics", "electricity", "electromagnetism"]


def _infer_subject_family(problem: str, teaching_context: str) -> str:
    text = f"{problem}\n{teaching_context}".lower()
    if any(keyword in text for keyword in _PHYSICS_FAMILY_KEYWORDS):
        return "physics"
    # 预留后续扩展: math / chemistry / ...
    return "unknown"


def _resolve_domains_for_components(problem: str, teaching_plan: dict[str, Any] | None) -> tuple[str, list[str]]:
    teaching_context = _teaching_plan_context_text(teaching_plan)
    family = _infer_subject_family(problem, teaching_context)
    if family == "physics":
        return family, ["mechanics", "electricity", "electromagnetism"]
    return family, _infer_domains(problem, teaching_context)


def _domain_types(domain: str) -> set[str]:
    if domain == "mechanics":
        return set(_MECHANICS_TYPES)
    if domain == "electricity":
        return set(_ELECTRICITY_TYPES)
    if domain == "electromagnetism":
        return set(_ELECTROMAG_TYPES)
    return set()


def _build_component_cards(domains: list[str]) -> dict[str, dict[str, Any]]:
    selected_types: set[str] = set()
    for domain in domains:
        selected_types.update(_domain_types(domain))

    if not selected_types:
        selected_types = set(PHYSICS_OBJECT_PARAM_SPECS.keys())

    cards: dict[str, dict[str, Any]] = {}
    for object_type in sorted(selected_types):
        params = list(PHYSICS_OBJECT_PARAM_SPECS.get(object_type, ()))
        if object_type in _MECHANICS_TYPES:
            domain = "mechanics"
        elif object_type in _ELECTRICITY_TYPES:
            domain = "electricity"
        else:
            domain = "electromagnetism"

        label = _COMPONENT_LABELS.get(object_type, object_type)
        purpose = _COMPONENT_PURPOSES.get(object_type, f"用于 {domain} 场景中的 {label} 表达。")
        key_params = params[: min(4, len(params))]
        cards[object_type] = {
            "domain": domain,
            "label": label,
            "purpose": purpose,
            "key_params": key_params,
            "all_params": params,
            "when_to_use": f"题意需要 {label} 的结构或关系时。",
            "avoid_when": "不要把它当作通用占位符；若与题意无关则不要使用。",
        }
    return cards


def _validate_known_param_keys(path: str, obj_type: str, params: dict[str, Any]) -> list[str]:
    allowed = PHYSICS_OBJECT_PARAM_SPECS.get(obj_type)
    if allowed is None:
        return []
    unknown = sorted([k for k in params.keys() if k not in set(allowed)])
    if not unknown:
        return []
    return [f"{path} has unknown params: {', '.join(unknown)}"]


def _prevalidate_composite_graph_raw(*, path: str, graph: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    parts = graph.get("parts")
    tracks = graph.get("tracks")
    constraints = graph.get("constraints")

    part_ids: set[str] = set()
    part_type_by_id: dict[str, str] = {}
    if isinstance(parts, list):
        for item in parts:
            if not isinstance(item, dict):
                continue
            part_id = item.get("id")
            if not isinstance(part_id, str) or not part_id.strip():
                continue
            normalized = part_id.strip()
            part_ids.add(normalized)
            part_type_by_id[normalized] = str(item.get("type", "")).strip()

    track_ids: set[str] = set()
    track_part_links: dict[str, str] = {}
    if isinstance(tracks, list):
        for item in tracks:
            if not isinstance(item, dict):
                continue
            track_id = item.get("id")
            if not isinstance(track_id, str) or not track_id.strip():
                continue
            track_key = track_id.strip()
            track_ids.add(track_key)

            data = item.get("data")
            if isinstance(data, dict):
                part_ref = data.get("part_id")
                if isinstance(part_ref, str) and part_ref.strip():
                    track_part_links[track_key] = part_ref.strip()

    if isinstance(constraints, list):
        for index, constraint in enumerate(constraints):
            if not isinstance(constraint, dict):
                continue
            c_type = str(constraint.get("type", "")).strip()
            if c_type != "attach":
                continue
            args = constraint.get("args")
            if not isinstance(args, dict):
                continue
            for key_name in (
                "part_a",
                "part_b",
                "from_part_id",
                "to_part_id",
                "source_part_id",
                "target_part_id",
                "part_id",
            ):
                value = args.get(key_name)
                if not isinstance(value, str) or not value.strip():
                    continue
                normalized_value = value.strip()
                if normalized_value not in track_ids:
                    continue
                hint = (
                    f"{path}.params.graph.constraints[{index}].args.{key_name}='{normalized_value}' "
                    "looks like a track id. attach requires part ids from graph.parts[].id."
                )
                part_link = track_part_links.get(normalized_value)
                if part_link and part_link in part_ids:
                    hint += f" Use '{part_link}' instead."
                elif normalized_value.startswith("t_"):
                    candidate = f"p_{normalized_value[2:]}"
                    if candidate in part_ids:
                        hint += f" Use '{candidate}' instead."
                errors.append(hint)

    has_arc_track = False
    if isinstance(tracks, list):
        has_arc_track = any(isinstance(item, dict) and str(item.get("type", "")).strip() == "arc" for item in tracks)
    has_curved_part = any(part_type_by_id.get(pid) in _CURVED_PART_TYPES for pid in part_type_by_id)
    if has_arc_track and not has_curved_part:
        errors.append(
            f"{path}.params.graph has arc track(s) but no curved part in graph.parts "
            f"(expected one of: {', '.join(sorted(_CURVED_PART_TYPES))})"
        )

    return errors


def _validate_composite_graph(
    *,
    path: str,
    params: dict[str, Any],
    allowed_object_types: set[str],
    require_motion: bool = False,
) -> list[str]:
    graph = params.get("graph")
    if graph is None:
        return [f"{path} needs params.graph"]
    if not isinstance(graph, dict):
        return [f"{path} params.graph must be an object"]

    pre_errors = _prevalidate_composite_graph_raw(path=path, graph=graph)

    try:
        model = CompositeGraph.model_validate(graph)
    except Exception as exc:  # noqa: BLE001
        if pre_errors:
            return pre_errors
        return [f"{path} invalid params.graph: {exc}"]

    errors: list[str] = list(pre_errors)
    allowed_part_types = set(allowed_object_types) - {"CompositeObject"}
    part_type_by_id: dict[str, str] = {}
    track_ids = {track.id for track in model.tracks}
    track_by_id = {track.id: track for track in model.tracks}
    movable_part_ids: set[str] = set()
    for index, part in enumerate(model.parts):
        part_path = f"{path}.params.graph.parts[{index}]"
        if part.type not in allowed_part_types:
            errors.append(f"{part_path}.type not allowed: {part.type}")
            continue
        part_type_by_id[part.id] = part.type
        if part.type in _MOVABLE_PART_TYPES:
            movable_part_ids.add(part.id)
        errors.extend(_validate_known_param_keys(part_path, part.type, part.params))

    _, anchors_raw, _ = _load_llm_constraints_assets()
    components_map = anchors_raw.get("components", {}) if isinstance(anchors_raw, dict) else {}

    def _allowed_anchor_set(part_id: str) -> set[str]:
        part_type = part_type_by_id.get(part_id)
        if not part_type:
            return set()
        entry = components_map.get(part_type)
        if not isinstance(entry, dict):
            return set()
        anchors = entry.get("anchors")
        if not isinstance(anchors, list):
            return set()
        return {str(x).strip().lower() for x in anchors if str(x).strip()}

    def _check_anchor(anchor_key: str, part_id: str | None, args: dict[str, Any], c_path: str) -> None:
        if anchor_key not in args:
            return
        anchor_name = args.get(anchor_key)
        if not isinstance(anchor_name, str):
            return
        if not part_id:
            return
        allowed = _allowed_anchor_set(part_id)
        if not allowed:
            return
        normalized_anchor = anchor_name.strip().lower()
        if normalized_anchor not in allowed:
            allowed_text = ", ".join(sorted(allowed))
            errors.append(
                f"{c_path}.args.{anchor_key} invalid for part '{part_id}': {anchor_name} (allowed: {allowed_text})"
            )

    def _check_track_anchor(anchor_key: str, part_id: str | None, data: dict[str, Any], t_path: str) -> None:
        if anchor_key not in data:
            return
        anchor_name = data.get(anchor_key)
        if not isinstance(anchor_name, str):
            return
        if not part_id:
            return
        allowed = _allowed_anchor_set(part_id)
        if not allowed:
            return
        normalized_anchor = anchor_name.strip().lower()
        if normalized_anchor not in allowed:
            allowed_text = ", ".join(sorted(allowed))
            errors.append(
                f"{t_path}.data.{anchor_key} invalid for part '{part_id}': {anchor_name} (allowed: {allowed_text})"
            )

    def _validate_motion_timeline(
        *,
        motion_path: str,
        timeline: list[dict[str, Any]],
        key: str,
        require_non_decreasing_value: bool = False,
    ) -> list[tuple[float, float]]:
        if not timeline:
            errors.append(f"{motion_path}.timeline cannot be empty")
            return []
        if len(timeline) < 2:
            errors.append(f"{motion_path}.timeline must have at least 2 points")

        points: list[tuple[float, float]] = []
        prev_t: float | None = None
        prev_v: float | None = None
        for point_index, item in enumerate(timeline):
            point_path = f"{motion_path}.timeline[{point_index}]"
            if not isinstance(item, dict):
                errors.append(f"{point_path} must be an object")
                continue
            t_raw = item.get("t")
            t_value: float | None = None
            if not isinstance(t_raw, (int, float)):
                errors.append(f"{point_path}.t must be a number")
            else:
                t_value = float(t_raw)
                if prev_t is not None and t_value <= prev_t:
                    errors.append(f"{point_path}.t must be strictly increasing")
                prev_t = t_value

            v_value: float | None = None
            if key not in item:
                errors.append(f"{point_path} missing '{key}'")
            elif not isinstance(item.get(key), (int, float)):
                errors.append(f"{point_path}.{key} must be a number")
            else:
                v_value = float(item.get(key))

            if t_value is None or v_value is None:
                continue
            if require_non_decreasing_value and prev_v is not None and v_value < prev_v:
                errors.append(f"{point_path}.{key} must be non-decreasing")
            prev_v = v_value
            points.append((t_value, v_value))
        return points

    attach_part_pairs: set[frozenset[str]] = set()
    for constraint in model.constraints:
        if str(constraint.type).strip() != "attach":
            continue
        c_args = dict(constraint.args or {})
        part_a = c_args.get("part_a")
        part_b = c_args.get("part_b")
        if not isinstance(part_a, str) or not part_a.strip():
            continue
        if not isinstance(part_b, str) or not part_b.strip():
            continue
        attach_part_pairs.add(frozenset((part_a.strip(), part_b.strip())))

    def _track_endpoint(track_id: str, which: str) -> tuple[str, str | None] | None:
        track = track_by_id.get(track_id)
        if track is None:
            return None
        data = dict(track.data or {})
        part_id = data.get("part_id")
        if not isinstance(part_id, str) or not part_id.strip():
            return None
        if which == "start":
            anchor_raw = data.get("anchor_a", data.get("from_anchor", data.get("start_anchor")))
        else:
            anchor_raw = data.get("anchor_b", data.get("to_anchor", data.get("end_anchor")))
        anchor = str(anchor_raw).strip() if isinstance(anchor_raw, str) and anchor_raw.strip() else None
        return part_id.strip(), anchor

    for track_index, track in enumerate(model.tracks):
        t_path = f"{path}.params.graph.tracks[{track_index}]"
        t_data = dict(track.data or {})
        t_type = str(track.type).strip().lower()
        t_space = str(t_data.get("space", "local")).strip().lower()
        is_local = t_space != "world"
        t_part = t_data.get("part_id")
        part_id = t_part.strip() if isinstance(t_part, str) and t_part.strip() else None
        if is_local and part_id is None:
            errors.append(f"{t_path}.data(local) requires part_id")
            continue
        if part_id is None:
            continue

        if t_type in {"line", "segment"} and is_local:
            has_legacy_local_points = any(
                key in t_data for key in ("p1_local", "p2_local", "x1_local", "y1_local", "x2_local", "y2_local")
            )
            if has_legacy_local_points:
                errors.append(
                    f"{t_path}.data(line local) forbids p1_local/p2_local/x*_local; use anchor_a/anchor_b only"
                )

            anchor_a = t_data.get("anchor_a", t_data.get("a1"))
            anchor_b = t_data.get("anchor_b", t_data.get("a2"))
            if not isinstance(anchor_a, str) or not anchor_a.strip():
                errors.append(f"{t_path}.data(anchor_a) required for local line/segment")
            if not isinstance(anchor_b, str) or not anchor_b.strip():
                errors.append(f"{t_path}.data(anchor_b) required for local line/segment")

        if t_type == "arc" and is_local:
            has_center_anchor = isinstance(t_data.get("center_anchor"), str) and bool(str(t_data.get("center_anchor")).strip())
            has_center_xy_local = isinstance(t_data.get("cx_local"), (int, float)) and isinstance(
                t_data.get("cy_local"), (int, float)
            )
            if not (has_center_anchor or has_center_xy_local):
                errors.append(f"{t_path}.data(local arc) requires center_anchor or cx_local+cy_local")

            if not any(key in t_data for key in ("radius_local", "r_local")):
                errors.append(f"{t_path}.data(local arc) requires radius_local or r_local")

            has_local_angles = (
                ("start_deg_local" in t_data and "end_deg_local" in t_data)
                or ("start_angle_local" in t_data and "end_angle_local" in t_data)
            )
            if not has_local_angles:
                errors.append(f"{t_path}.data(local arc) requires start/end local angles")

        _check_track_anchor("anchor_a", part_id, t_data, t_path)
        _check_track_anchor("anchor_b", part_id, t_data, t_path)
        _check_track_anchor("a1", part_id, t_data, t_path)
        _check_track_anchor("a2", part_id, t_data, t_path)
        _check_track_anchor("center_anchor", part_id, t_data, t_path)

    for index, constraint in enumerate(model.constraints):
        c_path = f"{path}.params.graph.constraints[{index}]"
        for item in validate_constraint(constraint):
            errors.append(f"{c_path}: {item}")

        c_args = dict(constraint.args or {})

        part_id = c_args.get("part_id") if isinstance(c_args.get("part_id"), str) else None
        part_a = c_args.get("part_a") if isinstance(c_args.get("part_a"), str) else None
        part_b = c_args.get("part_b") if isinstance(c_args.get("part_b"), str) else None
        from_part = c_args.get("from_part_id") if isinstance(c_args.get("from_part_id"), str) else None
        to_part = c_args.get("to_part_id") if isinstance(c_args.get("to_part_id"), str) else None
        source_part = c_args.get("source_part_id") if isinstance(c_args.get("source_part_id"), str) else None
        target_part = c_args.get("target_part_id") if isinstance(c_args.get("target_part_id"), str) else None

        part_for_anchor = part_id or part_a or from_part or source_part
        part_for_anchor_a = part_a or from_part or source_part or part_id
        part_for_anchor_b = part_b or to_part or target_part
        part_for_anchor_1 = c_args.get("part_1") if isinstance(c_args.get("part_1"), str) else None
        part_for_anchor_2 = c_args.get("part_2") if isinstance(c_args.get("part_2"), str) else None

        _check_anchor("anchor", part_for_anchor, c_args, c_path)
        _check_anchor("anchor_a", part_for_anchor_a, c_args, c_path)
        _check_anchor("from_anchor", part_for_anchor_a, c_args, c_path)
        _check_anchor("anchor_b", part_for_anchor_b, c_args, c_path)
        _check_anchor("to_anchor", part_for_anchor_b, c_args, c_path)
        _check_anchor("anchor_1", part_for_anchor_1, c_args, c_path)
        _check_anchor("anchor_2", part_for_anchor_2, c_args, c_path)

    allowed_motion_types = {"on_track", "on_track_schedule"}
    moved_part_ids: set[str] = set()
    for index, motion in enumerate(model.motions):
        m_path = f"{path}.params.graph.motions[{index}]"
        motion_type = str(motion.type).strip()
        if motion_type not in allowed_motion_types:
            errors.append(
                f"{m_path}.type not allowed: {motion.type} (allowed: on_track, on_track_schedule)"
            )
            continue

        m_args = dict(motion.args or {})
        part_id = m_args.get("part_id")
        if not isinstance(part_id, str) or not part_id.strip():
            errors.append(f"{m_path}.args.part_id required")
            continue
        part_id = part_id.strip()
        if part_id not in part_type_by_id:
            errors.append(f"{m_path}.args.part_id unknown: {part_id}")
            continue
        moved_part_ids.add(part_id)

        _check_anchor("anchor", part_id, m_args, m_path)

        default_key = "s" if motion_type == "on_track" else "u"
        param_key_raw = m_args.get("param_key", default_key)
        param_key = str(param_key_raw).strip() if param_key_raw is not None else default_key
        if not param_key:
            errors.append(f"{m_path}.args.param_key cannot be empty")
            param_key = default_key
        timeline_points = _validate_motion_timeline(
            motion_path=m_path,
            timeline=motion.timeline,
            key=param_key,
            require_non_decreasing_value=(motion_type == "on_track_schedule"),
        )

        if motion_type == "on_track":
            track_id = m_args.get("track_id")
            if not isinstance(track_id, str) or not track_id.strip():
                errors.append(f"{m_path}.args.track_id required for on_track")
            elif track_id.strip() not in track_ids:
                errors.append(f"{m_path}.args.track_id unknown: {track_id}")
            continue

        segments = m_args.get("segments")
        if not isinstance(segments, list) or not segments:
            errors.append(f"{m_path}.args.segments must be a non-empty list for on_track_schedule")
            continue

        normalized_segments: list[tuple[float, float, str]] = []
        for seg_index, segment in enumerate(segments):
            seg_path = f"{m_path}.args.segments[{seg_index}]"
            if not isinstance(segment, dict):
                errors.append(f"{seg_path} must be an object")
                continue

            track_id = segment.get("track_id")
            if not isinstance(track_id, str) or not track_id.strip():
                errors.append(f"{seg_path}.track_id required")
                continue
            track_id = track_id.strip()
            if track_id not in track_ids:
                errors.append(f"{seg_path}.track_id unknown: {track_id}")
                continue

            u0_raw = segment.get("u0")
            u1_raw = segment.get("u1")
            if not isinstance(u0_raw, (int, float)):
                errors.append(f"{seg_path}.u0 must be a number")
                continue
            if not isinstance(u1_raw, (int, float)):
                errors.append(f"{seg_path}.u1 must be a number")
                continue
            u0 = float(u0_raw)
            u1 = float(u1_raw)
            if u1 <= u0:
                errors.append(f"{seg_path} requires u1 > u0")
                continue

            normalized_segments.append((u0, u1, track_id))
            for key_name in ("s0", "s1"):
                if key_name in segment and not isinstance(segment.get(key_name), (int, float)):
                    errors.append(f"{seg_path}.{key_name} must be a number")

        if not normalized_segments:
            continue

        for seg_index in range(1, len(normalized_segments)):
            prev_u1 = normalized_segments[seg_index - 1][1]
            curr_u0 = normalized_segments[seg_index][0]
            if abs(curr_u0 - prev_u1) > 1e-6:
                errors.append(f"{m_path}.args.segments must be continuous in u (segment {seg_index - 1}->{seg_index})")

            prev_track = normalized_segments[seg_index - 1][2]
            curr_track = normalized_segments[seg_index][2]
            if prev_track == curr_track:
                continue
            prev_end = _track_endpoint(prev_track, "end")
            curr_start = _track_endpoint(curr_track, "start")
            if prev_end is None or curr_start is None:
                continue
            prev_part, _ = prev_end
            curr_part, _ = curr_start
            if prev_part == curr_part:
                continue
            if frozenset((prev_part, curr_part)) not in attach_part_pairs:
                errors.append(
                    f"{m_path}.args.segments[{seg_index}] switches track '{prev_track}' -> '{curr_track}' "
                    f"without attach link between parts '{prev_part}' and '{curr_part}'"
                )

        if timeline_points:
            values = [item[1] for item in timeline_points]
            min_u = min(values)
            max_u = max(values)
            first_u0 = normalized_segments[0][0]
            last_u1 = normalized_segments[-1][1]
            if min_u > first_u0 + 1e-6:
                errors.append(f"{m_path}.timeline {param_key} starts after first segment.u0")
            if max_u < last_u1 - 1e-6:
                errors.append(f"{m_path}.timeline {param_key} ends before last segment.u1")

    if require_motion and movable_part_ids and model.tracks:
        if not model.motions:
            errors.append(f"{path}.params.graph.motions is required for dynamic scene")
        elif not (moved_part_ids & movable_part_ids):
            errors.append(
                f"{path}.params.graph.motions does not drive movable parts: {', '.join(sorted(movable_part_ids))}"
            )

    return errors


def validate_scene_draft_data(data: Any, *, allowed_object_types: set[str]) -> list[str]:
    try:
        draft = SceneDraft.model_validate(data)
    except Exception as exc:  # noqa: BLE001
        return [f"scene_draft schema invalid: {exc}"]

    errors: list[str] = []
    object_defs: dict[str, str] = {}
    pedagogy = draft.pedagogy_plan
    budget = pedagogy.cognitive_budget if pedagogy is not None else None
    has_check_scene = False
    allowed_scene_roles = {"diagram", "title", "core_eq", "support_eq", "conclusion", "check", "hint"}

    for scene_index, scene in enumerate(draft.scenes):
        path = f"scenes[{scene_index}]"
        scene_requires_motion = _scene_requires_motion(scene)
        if len(scene.objects) > 9:
            errors.append(f"{path}.objects has {len(scene.objects)} items, exceeds max 9")
        if budget is not None and len(scene.objects) > budget.max_visible_objects:
            errors.append(
                f"{path}.objects has {len(scene.objects)} items, exceeds pedagogy budget max_visible_objects={budget.max_visible_objects}"
            )
        if pedagogy is not None and pedagogy.need_single_goal and not (scene.goal or "").strip():
            errors.append(f"{path}.goal required when pedagogy_plan.need_single_goal=true")
        if scene.is_check_scene:
            has_check_scene = True
            if "check" not in {m.strip().lower() for m in scene.modules}:
                errors.append(f"{path} is_check_scene=true but modules does not include 'check'")
            if not (scene.goal or "").strip():
                errors.append(f"{path} is_check_scene=true but goal is empty")
            if pedagogy is not None and not pedagogy.check_types:
                errors.append(f"{path} is_check_scene=true but pedagogy_plan.check_types is empty")

        formula_count = 0
        scene_object_ids = {obj.id for obj in scene.objects}
        if budget is not None and len(scene.new_symbols) > budget.max_new_symbols:
            errors.append(
                f"{path}.new_symbols has {len(scene.new_symbols)} items, exceeds pedagogy budget max_new_symbols={budget.max_new_symbols}"
            )
        for object_id, role in scene.roles.items():
            if object_id not in scene_object_ids:
                errors.append(f"{path}.roles references unknown scene object id: {object_id}")
            normalized_role = str(role).strip().lower()
            if normalized_role not in allowed_scene_roles:
                errors.append(f"{path}.roles[{object_id}] has unknown role: {role}")

        seen_ids_in_scene: set[str] = set()
        for object_index, obj in enumerate(scene.objects):
            obj_path = f"{path}.objects[{object_index}]"

            if obj.id in seen_ids_in_scene:
                errors.append(f"{obj_path}.id duplicated in same scene: {obj.id}")
            else:
                seen_ids_in_scene.add(obj.id)

            serialized = json.dumps(obj.model_dump(mode="json"), ensure_ascii=False, sort_keys=True)
            if obj.id in object_defs and object_defs[obj.id] != serialized:
                errors.append(f"{obj_path}.id redefined with different content: {obj.id}")
            else:
                object_defs.setdefault(obj.id, serialized)

            if obj.type not in allowed_object_types:
                errors.append(f"{obj_path}.type not allowed: {obj.type}")
                continue

            if obj.type not in _TOP_LEVEL_OBJECT_TYPES:
                errors.append(
                    f"{obj_path}.type should be wrapped by CompositeObject at top level: {obj.type}"
                )

            if obj.type == "TextBlock":
                text = obj.params.get("text")
                content = obj.params.get("content")
                if text is None and content is None:
                    errors.append(f"{obj_path} TextBlock needs params.text")
                else:
                    normalized_text = str(text if text is not None else content)
                    if budget is not None and len(normalized_text) > budget.max_text_chars:
                        errors.append(
                            f"{obj_path} TextBlock length {len(normalized_text)} exceeds pedagogy budget max_text_chars={budget.max_text_chars}"
                        )
                    if has_unbalanced_inline_math_delimiters(normalized_text):
                        errors.append(f"{obj_path} TextBlock has unbalanced $...$ delimiters")
                    if has_latex_tokens_outside_inline_math(normalized_text):
                        errors.append(f"{obj_path} TextBlock has LaTeX tokens outside $...$")

            if obj.type == "Formula":
                formula_count += 1
                latex = obj.params.get("latex")
                if latex is None:
                    errors.append(f"{obj_path} Formula needs params.latex")
                else:
                    latex_text = str(latex).strip()
                    if not latex_text:
                        errors.append(f"{obj_path} Formula params.latex cannot be empty")
                    if _contains_cjk(latex_text):
                        errors.append(f"{obj_path} Formula params.latex contains CJK; use TextBlock")

            if obj.type == "CompositeObject":
                errors.extend(
                    _validate_composite_graph(
                        path=obj_path,
                        params=obj.params,
                        allowed_object_types=allowed_object_types,
                        require_motion=scene_requires_motion,
                    )
                )

            errors.extend(_validate_known_param_keys(obj_path, obj.type, obj.params))

        if budget is not None and formula_count > budget.max_new_formula:
            errors.append(
                f"{path} has {formula_count} Formula objects, exceeds pedagogy budget max_new_formula={budget.max_new_formula}"
            )

    if pedagogy is not None and pedagogy.need_check_scene and not has_check_scene:
        errors.append("pedagogy_plan.need_check_scene=true but no scene has is_check_scene=true")

    return errors


def _is_formula_char(ch: str) -> bool:
    if not ch:
        return False
    if ch.isascii() and ch.isalnum():
        return True
    return ch in {"_", "^", "{", "}", "\\", "=", "+", "-", "*", "/", "(", ")", ".", ",", ":", ";", "<", ">", "|", "'", '"', " "}


def _wrap_latex_in_text_segment(segment: str) -> str:
    if not segment or not _LATEX_CMD_RE.search(segment):
        return segment

    out: list[str] = []
    cursor = 0
    seg_len = len(segment)

    while True:
        m = _LATEX_CMD_RE.search(segment, cursor)
        if m is None:
            break

        left = m.start()
        right = m.end()

        while left > cursor and _is_formula_char(segment[left - 1]):
            left -= 1
        while right < seg_len and _is_formula_char(segment[right]):
            right += 1

        while left < right and segment[left].isspace():
            left += 1
        while right > left and segment[right - 1].isspace():
            right -= 1

        if right <= cursor:
            cursor = max(cursor + 1, m.end())
            continue
        if left < cursor:
            left = cursor

        if left > cursor:
            out.append(segment[cursor:left])

        chunk = segment[left:right]
        if chunk:
            out.append(f"${chunk}$")
            cursor = right
        else:
            cursor = max(cursor + 1, m.end())

    if cursor < seg_len:
        out.append(segment[cursor:])

    return "".join(out)


def _force_wrap_latex_commands_outside_math(text: str) -> str:
    rebuilt: list[str] = []
    for kind, value in split_inline_math_segments(text):
        if kind == "math":
            rebuilt.append(f"${value}$")
            continue
        rebuilt.append(_LATEX_TOKEN_RE.sub(lambda m: f"${m.group(0)}$", value))
    return "".join(rebuilt)


def _auto_fix_textblock_inline_math(text: str) -> tuple[str, bool]:
    original = str(text)
    if not has_latex_tokens_outside_inline_math(original):
        return original, False

    rebuilt: list[str] = []
    for kind, value in split_inline_math_segments(original):
        if kind == "math":
            rebuilt.append(f"${value}$")
            continue
        rebuilt.append(_wrap_latex_in_text_segment(value))
    candidate = "".join(rebuilt)

    if has_latex_tokens_outside_inline_math(candidate):
        candidate = _force_wrap_latex_commands_outside_math(candidate)

    if has_unbalanced_inline_math_delimiters(candidate):
        plain = candidate.replace("$", "")
        candidate = _force_wrap_latex_commands_outside_math(plain)

    if has_latex_tokens_outside_inline_math(candidate):
        # Last resort: neutralize command prefix to avoid validation hard-fail.
        candidate = _LATEX_CMD_RE.sub(lambda m: m.group(0).replace("\\", "/"), candidate)

    return candidate, candidate != original


def _normalize_scene_role(object_id: str, role: str) -> str:
    allowed = {"diagram", "title", "core_eq", "support_eq", "conclusion", "check", "hint"}
    normalized = str(role).strip().lower()
    if normalized in allowed:
        return normalized

    alias = {
        "equation": "core_eq",
        "formula": "core_eq",
        "model": "support_eq",
        "solve": "conclusion",
        "result": "conclusion",
        "summary": "conclusion",
        "checking": "check",
        "check_scene": "check",
    }
    if normalized in alias:
        return alias[normalized]

    object_id_norm = str(object_id).strip().lower()
    if "diagram" in object_id_norm:
        return "diagram"
    if "title" in object_id_norm:
        return "title"
    if "eq" in object_id_norm or "formula" in object_id_norm:
        return "core_eq"
    if "check" in object_id_norm:
        return "check"
    return "support_eq"


def _auto_fix_attach_track_part_refs(graph: dict[str, Any]) -> bool:
    parts = graph.get("parts")
    tracks = graph.get("tracks")
    constraints = graph.get("constraints")
    if not isinstance(parts, list) or not isinstance(tracks, list) or not isinstance(constraints, list):
        return False

    part_ids: set[str] = set()
    part_type_by_id: dict[str, str] = {}
    for part in parts:
        if not isinstance(part, dict):
            continue
        part_id = part.get("id")
        if not isinstance(part_id, str) or not part_id.strip():
            continue
        normalized = part_id.strip()
        part_ids.add(normalized)
        part_type_by_id[normalized] = str(part.get("type", "")).strip()

    track_to_part: dict[str, str] = {}
    track_by_id: dict[str, dict[str, Any]] = {}
    for track in tracks:
        if not isinstance(track, dict):
            continue
        track_id = track.get("id")
        if not isinstance(track_id, str) or not track_id.strip():
            continue
        track_key = track_id.strip()
        track_by_id[track_key] = track
        data = track.get("data")
        if not isinstance(data, dict):
            continue
        part_ref = data.get("part_id")
        if isinstance(part_ref, str) and part_ref.strip() in part_ids:
            track_to_part[track_key] = part_ref.strip()

    curved_parts = [pid for pid, ptype in part_type_by_id.items() if ptype in _CURVED_PART_TYPES]
    changed = False

    def _to_float(value: Any, default: float) -> float:
        try:
            return float(value)
        except Exception:  # noqa: BLE001
            return default

    def _derive_arc_angles(data: dict[str, Any]) -> tuple[float, float]:
        start_angle = _to_float(data.get("start_angle", data.get("start_deg", data.get("a0", 0.0))), 0.0)
        end_angle = _to_float(data.get("end_angle", data.get("end_deg", data.get("a1", 90.0))), 90.0)
        return start_angle, end_angle

    def _derive_center(data: dict[str, Any]) -> tuple[float, float, float]:
        center = data.get("center")
        if isinstance(center, dict):
            cx = _to_float(center.get("x"), 0.0)
            cy = _to_float(center.get("y"), 0.0)
            return cx, cy, 0.0
        if isinstance(center, (list, tuple)) and len(center) >= 2:
            cx = _to_float(center[0], 0.0)
            cy = _to_float(center[1], 0.0)
            cz = _to_float(center[2], 0.0) if len(center) >= 3 else 0.0
            return cx, cy, cz
        cx = _to_float(data.get("cx"), 0.0)
        cy = _to_float(data.get("cy"), 0.0)
        return cx, cy, 0.0

    def _ensure_arc_part_from_track(track_id: str) -> str | None:
        track = track_by_id.get(track_id)
        if not isinstance(track, dict):
            return None
        track_type = str(track.get("type", "")).strip()
        if track_type != "arc":
            return None

        candidate = f"p_{track_id[2:]}" if track_id.startswith("t_") else f"p_{track_id}"
        new_id = candidate
        suffix = 1
        while new_id in part_ids:
            suffix += 1
            new_id = f"{candidate}_{suffix}"

        data = track.get("data")
        if not isinstance(data, dict):
            data = {}
            track["data"] = data
        cx, cy, cz = _derive_center(data)
        radius = _to_float(data.get("radius"), 1.0)
        start_angle, end_angle = _derive_arc_angles(data)

        part = {
            "id": new_id,
            "type": "ArcTrack",
            "params": {
                "center": [cx, cy, cz],
                "radius": radius,
                "start_angle": start_angle,
                "end_angle": end_angle,
            },
            "style": {},
            "seed_pose": {"x": cx, "y": cy, "theta": 0.0, "scale": 1.0},
        }
        parts.append(part)
        part_ids.add(new_id)
        part_type_by_id[new_id] = "ArcTrack"
        track_to_part[track_id] = new_id
        if "part_id" not in data:
            data["part_id"] = new_id
        if "anchor_a" not in data and "from_anchor" not in data and "start_anchor" not in data:
            data["anchor_a"] = "start"
        if "anchor_b" not in data and "to_anchor" not in data and "end_anchor" not in data:
            data["anchor_b"] = "end"
        return new_id

    for constraint in constraints:
        if not isinstance(constraint, dict):
            continue
        if str(constraint.get("type", "")).strip() != "attach":
            continue
        args = constraint.get("args")
        if not isinstance(args, dict):
            continue

        for key_name in ("part_a", "part_b", "from_part_id", "to_part_id", "source_part_id", "target_part_id"):
            value = args.get(key_name)
            if not isinstance(value, str) or not value.strip():
                continue
            normalized_value = value.strip()
            if normalized_value in part_ids:
                continue

            mapped_part = track_to_part.get(normalized_value)
            if mapped_part is None and normalized_value.startswith("t_"):
                candidate = f"p_{normalized_value[2:]}"
                if candidate in part_ids:
                    mapped_part = candidate

            if mapped_part is None and "arc" in normalized_value.lower() and len(curved_parts) == 1:
                mapped_part = curved_parts[0]

            if mapped_part is None and normalized_value in track_by_id:
                mapped_part = _ensure_arc_part_from_track(normalized_value)

            if mapped_part is None:
                continue

            args[key_name] = mapped_part
            changed = True

    return changed


def normalize_scene_draft_data(data: Any) -> tuple[dict[str, Any] | None, bool]:
    if not isinstance(data, dict):
        return None, False

    changed = False
    scenes = data.get("scenes")
    if not isinstance(scenes, list):
        return data, changed

    for scene in scenes:
        if not isinstance(scene, dict):
            continue
        goal = scene.get("goal")
        if goal is not None and not isinstance(goal, str):
            scene["goal"] = str(goal)
            changed = True

        modules = scene.get("modules")
        if isinstance(modules, list):
            normalized_modules = [str(x).strip() for x in modules if str(x).strip()]
            if normalized_modules != modules:
                scene["modules"] = normalized_modules
                changed = True

        roles = scene.get("roles")
        if isinstance(roles, dict):
            normalized_roles: dict[str, str] = {}
            for raw_key, raw_value in roles.items():
                key = str(raw_key).strip()
                value = _normalize_scene_role(key, str(raw_value))
                if key and value:
                    normalized_roles[key] = value
            if normalized_roles != roles:
                scene["roles"] = normalized_roles
                changed = True

        new_symbols = scene.get("new_symbols")
        if isinstance(new_symbols, list):
            normalized_symbols = [str(x).strip() for x in new_symbols if str(x).strip()]
            if normalized_symbols != new_symbols:
                scene["new_symbols"] = normalized_symbols
                changed = True

        is_check_scene = scene.get("is_check_scene")
        if is_check_scene is not None and not isinstance(is_check_scene, bool):
            scene["is_check_scene"] = bool(is_check_scene)
            changed = True

        objects = scene.get("objects")
        if not isinstance(objects, list):
            continue

        for obj in objects:
            if not isinstance(obj, dict):
                continue
            obj_type = obj.get("type")
            params = obj.get("params")
            if not isinstance(params, dict):
                continue

            if obj_type == "TextBlock":
                text = params.get("text")
                if text is None:
                    text = params.get("content", "")
                normalized_text = str(text)
                fixed_text, fixed = _auto_fix_textblock_inline_math(normalized_text)
                if fixed:
                    normalized_text = fixed_text
                    changed = True
                if params.get("text") != normalized_text:
                    params["text"] = normalized_text
                    changed = True
                if "content" in params:
                    params.pop("content", None)
                    changed = True
                continue

            if obj_type == "Formula":
                if "latex" not in params and "content" in params:
                    params["latex"] = str(params.get("content", ""))
                    params.pop("content", None)
                    changed = True
                latex = str(params.get("latex", "")).strip()
                if _contains_cjk(latex):
                    fixed_text, _ = _auto_fix_textblock_inline_math(latex)
                    obj["type"] = "TextBlock"
                    obj["params"] = {"text": fixed_text}
                    changed = True
                    continue
                if params.get("latex") != latex:
                    params["latex"] = latex
                    changed = True
                continue

            if obj_type == "CompositeObject":
                graph = params.get("graph")
                if not isinstance(graph, dict):
                    continue
                space = graph.get("space")
                if isinstance(space, dict) and space.get("origin") not in {None, "center"}:
                    space["origin"] = "center"
                    changed = True
                if _auto_fix_attach_track_part_refs(graph):
                    changed = True

    pedagogy = data.get("pedagogy_plan")
    max_new_symbols_limit: int | None = None
    if isinstance(pedagogy, dict):
        difficulty = pedagogy.get("difficulty")
        if difficulty is not None:
            normalized_difficulty = str(difficulty).strip().lower()
            if normalized_difficulty in {"simple", "medium", "hard"} and normalized_difficulty != difficulty:
                pedagogy["difficulty"] = normalized_difficulty
                changed = True

        budget = pedagogy.get("cognitive_budget")
        if isinstance(budget, dict):
            raw_max_text_chars = budget.get("max_text_chars")
            try:
                max_text_chars = int(raw_max_text_chars)
            except (TypeError, ValueError):
                max_text_chars = 60
            if max_text_chars < 60:
                budget["max_text_chars"] = 60
                changed = True
            raw_max_new_symbols = budget.get("max_new_symbols")
            try:
                max_new_symbols_limit = max(0, int(raw_max_new_symbols))
            except (TypeError, ValueError):
                max_new_symbols_limit = None

    if max_new_symbols_limit is not None and isinstance(scenes, list):
        for scene in scenes:
            if not isinstance(scene, dict):
                continue
            new_symbols = scene.get("new_symbols")
            if isinstance(new_symbols, list) and len(new_symbols) > max_new_symbols_limit:
                scene["new_symbols"] = new_symbols[:max_new_symbols_limit]
                changed = True

    return data, changed


def _compact_teaching_plan(teaching_plan: Any) -> dict[str, Any] | None:
    if not isinstance(teaching_plan, dict):
        return None

    sub_questions_compact: list[dict[str, Any]] = []
    for item in teaching_plan.get("sub_questions") or []:
        if not isinstance(item, dict):
            continue

        scene_packets = []
        for packet in item.get("scene_packets") or []:
            if not isinstance(packet, dict):
                continue
            content_items = packet.get("content_items")
            primary_item = packet.get("primary_item")
            scene_packets.append(
                {
                    "content_items": content_items if isinstance(content_items, list) else [],
                    "primary_item": str(primary_item).strip() if primary_item is not None else "",
                }
            )

        method_choice = item.get("method_choice")
        sub_questions_compact.append(
            {
                "id": str(item.get("id", "")).strip(),
                "goal": str(item.get("goal", "")).strip(),
                "given_conditions": item.get("given_conditions") if isinstance(item.get("given_conditions"), list) else [],
                "method_choice": method_choice if isinstance(method_choice, dict) else {},
                "result": item.get("result") if isinstance(item.get("result"), dict) else {},
                "sanity_checks": item.get("sanity_checks") if isinstance(item.get("sanity_checks"), list) else [],
                "scene_packets": scene_packets,
            }
        )

    return {
        "global_symbols": teaching_plan.get("global_symbols") if isinstance(teaching_plan.get("global_symbols"), list) else [],
        "sub_questions": sub_questions_compact,
    }



def _build_user_payload(
    *,
    problem: str,
    teaching_plan: dict[str, Any] | None,
    allowed_object_types: set[str],
) -> str:
    top_level_allowed = [x for x in _TOP_LEVEL_OBJECT_TYPES if x in allowed_object_types]
    subject_family, domains = _resolve_domains_for_components(problem, teaching_plan)
    cards = _build_component_cards(domains)
    domain_types = set(cards.keys())
    part_types = sorted(
        t
        for t in (set(allowed_object_types) - {"CompositeObject"})
        if t in domain_types or t in {"TextBlock", "Formula", "BulletPanel"}
    )

    compact_teaching_plan = _compact_teaching_plan(teaching_plan)
    constraint_bundle = _build_constraint_prompt_bundle(part_types=part_types, domains=domains)
    components_catalog = _build_components_catalog_for_prompt(part_types, domains)
    constraint_display = _constraints_for_prompt_display(constraint_bundle["constraints_whitelist"])
    protocol_bundle = _build_protocol_bundle_for_prompt(domains)

    lines = [
        "Allowed top-level object.type:",
        json.dumps(top_level_allowed, ensure_ascii=False),
        "",
        "Allowed CompositeObject part.type:",
        json.dumps(part_types, ensure_ascii=False),
        "",
        "Inferred subject domains:",
        json.dumps(domains, ensure_ascii=False),
        "",
        "Inferred subject family:",
        json.dumps(subject_family, ensure_ascii=False),
        "",
        "Component cards (domain relevant):",
        json.dumps(cards, ensure_ascii=False, indent=2),
        "",
        "Components catalog (from llm_constraints/specs/components_catalog.json):",
        json.dumps(components_catalog, ensure_ascii=False, indent=2),
        "",
        "Component params whitelist:",
        json.dumps(_physics_param_catalog(), ensure_ascii=False, indent=2),
        "",
        "Constraint whitelist (LLM must only use these constraint types/args):",
        json.dumps(constraint_display, ensure_ascii=False, indent=2),
        "",
        "Allowed constraint types:",
        json.dumps(constraint_bundle["allowed_constraint_types"], ensure_ascii=False),
        "",
        "Anchors dictionary (for current allowed part types):",
        json.dumps(constraint_bundle["anchors_dictionary"], ensure_ascii=False, indent=2),
        "",
        "Drawing protocol bundle (append-only guidance from llm_constraints/*.md):",
        json.dumps(protocol_bundle["files"], ensure_ascii=False),
        "",
        "Keep original prompt requirements, and additionally satisfy these protocol docs:",
        "",
        "Teaching content item catalog (from LLM1 scene_packets):",
        json.dumps(
            [
                "hook_question",
                "goal",
                "knowns",
                "diagram",
                "assumption",
                "principle",
                "core_equation",
                "derive_step",
                "substitute_compute",
                "intermediate_result",
                "conclusion",
                "check_sanity",
                "transition",
            ],
            ensure_ascii=False,
        ),
        "",
    ]

    for filename, content in protocol_bundle["docs"].items():
        lines.extend([f"[{filename}]", content, ""])

    if compact_teaching_plan is not None:
        lines.extend(
            [
                "teaching_plan.json (from LLM1, use as primary teaching structure guidance):",
                json.dumps(compact_teaching_plan, ensure_ascii=False, indent=2),
                "",
                "When teaching_plan is present, align scenes with sub_questions and scene_packets as much as possible.",
                "Each scene should have one primary focus and avoid stacking too many unrelated items.",
                "",
            ]
        )

    example = {
        "pedagogy_plan": {
            "difficulty": "medium",
            "need_single_goal": True,
            "need_check_scene": False,
            "check_types": ["feasibility"],
            "cognitive_budget": {
                "max_visible_objects": 4,
                "max_new_formula": 4,
                "max_new_symbols": 3,
                "max_text_chars": 60,
            },
            "module_order": ["diagram", "model", "equation", "solve", "conclusion"],
        },
        "scenes": [
            {
                "id": "S1",
                "intent": "Build the problem diagram.",
                "goal": "Show structure and given conditions.",
                "modules": ["diagram", "model"],
                "roles": {"o_title": "title", "o_diagram": "diagram"},
                "new_symbols": [],
                "is_check_scene": False,
                "objects": [
                    {
                        "id": "o_title",
                        "type": "TextBlock",
                        "params": {"text": "????"},
                        "style": {"size_level": "M"},
                        "priority": 1,
                    },
                    {
                        "id": "o_diagram",
                        "type": "CompositeObject",
                        "params": {
                            "graph": {
                                "version": "0.1",
                                "space": {
                                    "x_range": [-10, 10],
                                    "y_range": [-6, 6],
                                    "unit": "scene_unit",
                                    "angle_unit": "deg",
                                    "origin": "center",
                                },
                                "parts": [
                                    {
                                        "id": "p_plane",
                                        "type": "Wall",
                                        "params": {"angle": 30, "length": 8.0},
                                        "style": {},
                                        "seed_pose": {"x": 0, "y": 0, "theta": 0, "scale": 1.0},
                                    },
                                    {
                                        "id": "p_block",
                                        "type": "Block",
                                        "params": {"width": 1.2, "height": 0.8},
                                        "style": {},
                                        "seed_pose": {"x": -2, "y": 1, "theta": 0, "scale": 1.0},
                                    },
                                ],
                                "tracks": [],
                                "constraints": [],
                                "motions": [],
                            }
                        },
                        "style": {"size_level": "XL"},
                        "priority": 1,
                    },
                ],
            }
        ],
    }

    lines.extend(
        [
            "problem.md:",
            problem.strip(),
            "",
            "teaching_plan.json:",
            json.dumps(compact_teaching_plan, ensure_ascii=False, indent=2) if compact_teaching_plan is not None else "{}",
            "",
            "Output contract:",
            "1) Output strict JSON only.",
            "2) Root object must include scenes array.",
            "3) Each scenes[].objects[] item must include id/type/params/style/priority.",
            "4) If pedagogy_plan exists, it must match the expected schema.",
            "5) Use CompositeObject for problem diagrams; do not place physics parts directly at top level.",
            "6) Stable ids across scenes: same id => identical object definition.",
            "7) If content changes, create a new id.",
            "8) TextBlock mixed formula must use $...$ for latex fragments.",
            "9) Formula.params.latex must be pure formula (no CJK).",
            "10) Respect cognitive budget: max 4 formulas per scene.",
            "11) If teaching_plan is provided, preserve teaching flow and scene focus.",
            "12) CompositeObject.graph.constraints[].type must be in Allowed constraint types.",
            "13) Constraint args must follow Constraint whitelist.",
            "14) Any anchor name used by constraints must come from Anchors dictionary.",
            "14.1) Do not assume bbox anchors (left_center/right_center/...) exist for every part.",
            "15) For dynamic process scenes, include graph.motions (not only on_track_pose).",
            "16) on_track_schedule.segments must be continuous in u, and timeline must be valid.",
            "17) If switching tracks in schedule, switch only across attached/connected parts.",
            "",
            "Minimal example:",
            json.dumps(example, ensure_ascii=False, indent=2),
            "",
            "Now output complete scene_draft JSON.",
        ]
    )

    return "\n".join(lines)


def _render_error_lines(errors: list[str], *, limit: int = 40) -> str:
    if not errors:
        return "(no validation errors)"
    lines = [f"- {err}" for err in errors[:limit]]
    if len(errors) > limit:
        lines.append(f"- ... and {len(errors) - limit} more errors")
    return "\n".join(lines)



def _build_repair_payload(
    *,
    problem: str,
    teaching_plan: dict[str, Any] | None,
    allowed_object_types: set[str],
    raw_content: str,
    errors: list[str],
    round_index: int,
) -> str:
    top_level_allowed = [x for x in _TOP_LEVEL_OBJECT_TYPES if x in allowed_object_types]
    subject_family, domains = _resolve_domains_for_components(problem, teaching_plan)
    cards = _build_component_cards(domains)
    domain_types = set(cards.keys())
    part_types = sorted(
        t
        for t in (set(allowed_object_types) - {"CompositeObject"})
        if t in domain_types or t in {"TextBlock", "Formula", "BulletPanel"}
    )

    compact_teaching_plan = _compact_teaching_plan(teaching_plan)
    constraint_bundle = _build_constraint_prompt_bundle(part_types=part_types, domains=domains)
    components_catalog = _build_components_catalog_for_prompt(part_types, domains)
    constraint_display = _constraints_for_prompt_display(constraint_bundle["constraints_whitelist"])
    protocol_bundle = _build_protocol_bundle_for_prompt(domains)

    lines = [
        f"This is repair round {round_index}. Fix scene_draft.json with minimal changes.",
        "Output strict JSON only.",
        "",
        "Allowed top-level object.type:",
        json.dumps(top_level_allowed, ensure_ascii=False),
        "",
        "Allowed CompositeObject part.type:",
        json.dumps(part_types, ensure_ascii=False),
        "",
        "Inferred subject domains:",
        json.dumps(domains, ensure_ascii=False),
        "",
        "Inferred subject family:",
        json.dumps(subject_family, ensure_ascii=False),
        "",
        "Component cards:",
        json.dumps(cards, ensure_ascii=False, indent=2),
        "",
        "Components catalog (from llm_constraints/specs/components_catalog.json):",
        json.dumps(components_catalog, ensure_ascii=False, indent=2),
        "",
        "Component params whitelist:",
        json.dumps(_physics_param_catalog(), ensure_ascii=False, indent=2),
        "",
        "Constraint whitelist (LLM must only use these constraint types/args):",
        json.dumps(constraint_display, ensure_ascii=False, indent=2),
        "",
        "Allowed constraint types:",
        json.dumps(constraint_bundle["allowed_constraint_types"], ensure_ascii=False),
        "",
        "Anchors dictionary (for current allowed part types):",
        json.dumps(constraint_bundle["anchors_dictionary"], ensure_ascii=False, indent=2),
        "",
        "Drawing protocol bundle (append-only guidance from llm_constraints/*.md):",
        json.dumps(protocol_bundle["files"], ensure_ascii=False),
        "",
        "Repair must keep existing requirements and additionally satisfy these protocol docs:",
        "",
        "Validation errors to fix:",
        _render_error_lines(errors),
        "",
    ]

    for filename, content in protocol_bundle["docs"].items():
        lines.extend([f"[{filename}]", content, ""])

    if compact_teaching_plan is not None:
        lines.extend(
            [
                "teaching_plan.json (from LLM1):",
                json.dumps(compact_teaching_plan, ensure_ascii=False, indent=2),
                "",
                "Repair output must stay aligned with this teaching plan.",
                "",
            ]
        )

    lines.extend(
        [
            "problem.md:",
            problem.strip(),
            "",
            "teaching_plan.json:",
            json.dumps(compact_teaching_plan, ensure_ascii=False, indent=2) if compact_teaching_plan is not None else "{}",
            "",
            "Raw content to repair:",
            raw_content.strip(),
            "",
            "Repair requirements:",
            "- Root object must contain scenes array.",
            "- Keep ids stable; if content changes create new id.",
            "- cognitive_budget.max_text_chars >= 60.",
            "- TextBlock latex fragments must be inside $...$.",
            "- Max 4 Formula objects per scene.",
            "- constraints[].type must be in Allowed constraint types.",
            "- Constraint args must satisfy Constraint whitelist.",
            "- All anchor names must come from Anchors dictionary.",
            "- Do not assume bbox anchors exist for every part.",
            "- Dynamic process scenes must define graph.motions.",
            "- on_track_schedule requires continuous segments and valid timeline.",
            "- Output JSON only, no explanations.",
        ]
    )

    return "\n".join(lines)


def _parse_and_validate(content: str, *, allowed_object_types: set[str]) -> tuple[dict[str, Any] | None, list[str]]:
    try:
        data = load_json_from_llm(content)
    except Exception as exc:  # noqa: BLE001
        return None, [f"JSON parse failed: {exc}"]

    normalized, _ = normalize_scene_draft_data(data)
    if normalized is not None:
        data = normalized

    errors = validate_scene_draft_data(data, allowed_object_types=allowed_object_types)
    return (data if not errors else None), errors


def main() -> int:
    parser = argparse.ArgumentParser(description="LLM2: generate scene_draft.json")
    parser.add_argument("--case", default="cases/demo_001", help="Case directory, e.g. cases/demo_001")
    parser.add_argument("--no-repair", action="store_true", help="Skip repair when parse/validation fails")
    parser.add_argument("--continue-rounds", type=int, default=2, help="Max continuation rounds for truncated JSON")
    parser.add_argument("--repair-rounds", type=int, default=2, help="Max validation-driven repair rounds")
    args = parser.parse_args()

    load_dotenv()

    case_dir = Path(args.case)
    problem = (case_dir / "problem.md").read_text(encoding="utf-8")
    out_path = case_dir / "scene_draft.json"
    errors_path = case_dir / "llm2_validation_errors.txt"

    enums = load_enums()
    allowed_object_types = set(enums["object_types"])
    prompt = load_prompt("llm2_scene_draft.md")
    teaching_plan_path = case_dir / "teaching_plan.json"
    if not teaching_plan_path.exists():
        print(f"Missing required input for LLM2: {teaching_plan_path}", file=sys.stderr)
        return 2
    try:
        teaching_plan = json.loads(teaching_plan_path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        print(f"Invalid teaching_plan.json: {exc}", file=sys.stderr)
        return 2

    user_payload = _build_user_payload(
        problem=problem,
        teaching_plan=teaching_plan,
        allowed_object_types=allowed_object_types,
    )

    content = chat_completion([ChatMessage(role="system", content=prompt), ChatMessage(role="user", content=user_payload)])
    content, cont_chunks = continue_json_output(
        content,
        system_prompt=prompt,
        user_payload=user_payload,
        parse_fn=load_json_from_llm,
        max_rounds=args.continue_rounds,
    )

    raw_path = case_dir / "llm2_raw.txt"
    raw_path.write_text(content.strip() + "\n", encoding="utf-8")
    _write_continuation_chunks(case_dir, "llm2_continue_raw", cont_chunks)

    validation_log: list[str] = []
    data, errors = _parse_and_validate(content, allowed_object_types=allowed_object_types)
    if errors:
        validation_log.append("[initial]")
        validation_log.extend(errors)
        validation_log.append("")

    if errors and args.no_repair:
        errors_path.write_text("\n".join(validation_log).strip() + "\n", encoding="utf-8")
        print(
            "LLM2 output parse/validation failed. "
            f"See: {raw_path} and {errors_path}",
            file=sys.stderr,
        )
        return 2

    if errors:
        repair_prompt = load_prompt("json_repair.md")
        current_content = content
        repair_raw_path = case_dir / "llm2_repair_raw.txt"

        for round_index in range(1, max(1, args.repair_rounds) + 1):
            repair_payload = _build_repair_payload(
                problem=problem,
                teaching_plan=teaching_plan,
                allowed_object_types=allowed_object_types,
                raw_content=current_content,
                errors=errors,
                round_index=round_index,
            )
            repaired = chat_completion(
                [
                    ChatMessage(role="system", content=repair_prompt),
                    ChatMessage(role="user", content=repair_payload),
                ]
            )
            repaired, repair_cont_chunks = continue_json_output(
                repaired,
                system_prompt=repair_prompt,
                user_payload=repair_payload,
                parse_fn=load_json_from_llm,
                max_rounds=args.continue_rounds,
            )
            repair_raw_path.write_text(repaired.strip() + "\n", encoding="utf-8")
            (case_dir / f"llm2_repair_raw_round_{round_index}.txt").write_text(
                repaired.strip() + "\n", encoding="utf-8"
            )
            _write_continuation_chunks(case_dir, f"llm2_repair_continue_raw_r{round_index}", repair_cont_chunks)

            data, errors = _parse_and_validate(repaired, allowed_object_types=allowed_object_types)
            if errors:
                validation_log.append(f"[repair_round_{round_index}]")
                validation_log.extend(errors)
                validation_log.append("")
                current_content = repaired
                continue
            break

        if errors:
            errors_path.write_text("\n".join(validation_log).strip() + "\n", encoding="utf-8")
            print(
                "LLM2 repair rounds finished but output is still invalid. "
                f"See: {raw_path}, {repair_raw_path}, {errors_path}",
                file=sys.stderr,
            )
            return 2

    assert data is not None  # For type-checking; all error branches returned above.
    if errors_path.exists():
        errors_path.unlink()
    out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(str(out_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
