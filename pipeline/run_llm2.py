from __future__ import annotations

import argparse
import json
import re
import sys
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


_CJK_RE = re.compile(r"[\u3400-\u9fff]")
_LATEX_CMD_RE = re.compile(r"\\[a-zA-Z]+")
_LATEX_TOKEN_RE = re.compile(r"\\[a-zA-Z]+(?:\{[^{}]*\})?")
_TOP_LEVEL_OBJECT_TYPES = ("TextBlock", "BulletPanel", "Formula", "CompositeObject")

_MECHANICS_TYPES = {
    "InclinedPlaneGroup",
    "Wall",
    "InclinedPlane",
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
    "InclinedPlane": "斜面",
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
    "InclinedPlane": "表示斜面本体，常与 Block 组合。",
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


def _physics_param_catalog() -> dict[str, list[str]]:
    return {k: list(v) for k, v in sorted(PHYSICS_OBJECT_PARAM_SPECS.items())}


def _infer_domains(problem: str, explanation: str) -> list[str]:
    text = f"{problem}\n{explanation}".lower()
    scores: dict[str, int] = {}
    for domain, keywords in _DOMAIN_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw and kw.lower() in text)
        scores[domain] = score

    hit_domains = [d for d, s in scores.items() if s > 0]
    if hit_domains:
        return hit_domains
    return ["mechanics", "electricity", "electromagnetism"]


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


def _validate_composite_graph(
    *,
    path: str,
    params: dict[str, Any],
    allowed_object_types: set[str],
) -> list[str]:
    graph = params.get("graph")
    if graph is None:
        return [f"{path} needs params.graph"]
    if not isinstance(graph, dict):
        return [f"{path} params.graph must be an object"]

    try:
        model = CompositeGraph.model_validate(graph)
    except Exception as exc:  # noqa: BLE001
        return [f"{path} invalid params.graph: {exc}"]

    errors: list[str] = []
    allowed_part_types = set(allowed_object_types) - {"CompositeObject"}
    for index, part in enumerate(model.parts):
        part_path = f"{path}.params.graph.parts[{index}]"
        if part.type not in allowed_part_types:
            errors.append(f"{part_path}.type not allowed: {part.type}")
            continue
        errors.extend(_validate_known_param_keys(part_path, part.type, part.params))

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
    explanation: str,
    teaching_plan: dict[str, Any] | None,
    allowed_object_types: set[str],
) -> str:
    top_level_allowed = [x for x in _TOP_LEVEL_OBJECT_TYPES if x in allowed_object_types]
    domains = _infer_domains(problem, explanation)
    cards = _build_component_cards(domains)
    domain_types = set(cards.keys())
    part_types = sorted(
        t
        for t in (set(allowed_object_types) - {"CompositeObject"})
        if t in domain_types or t in {"TextBlock", "Formula", "BulletPanel"}
    )

    compact_teaching_plan = _compact_teaching_plan(teaching_plan)

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
        "Component cards (domain relevant):",
        json.dumps(cards, ensure_ascii=False, indent=2),
        "",
        "Component params whitelist:",
        json.dumps(_physics_param_catalog(), ensure_ascii=False, indent=2),
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
                                        "type": "InclinedPlane",
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
            "explanation.txt:",
            explanation.strip(),
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
    explanation: str,
    teaching_plan: dict[str, Any] | None,
    allowed_object_types: set[str],
    raw_content: str,
    errors: list[str],
    round_index: int,
) -> str:
    top_level_allowed = [x for x in _TOP_LEVEL_OBJECT_TYPES if x in allowed_object_types]
    domains = _infer_domains(problem, explanation)
    cards = _build_component_cards(domains)
    domain_types = set(cards.keys())
    part_types = sorted(
        t
        for t in (set(allowed_object_types) - {"CompositeObject"})
        if t in domain_types or t in {"TextBlock", "Formula", "BulletPanel"}
    )

    compact_teaching_plan = _compact_teaching_plan(teaching_plan)

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
        "Component cards:",
        json.dumps(cards, ensure_ascii=False, indent=2),
        "",
        "Component params whitelist:",
        json.dumps(_physics_param_catalog(), ensure_ascii=False, indent=2),
        "",
        "Validation errors to fix:",
        _render_error_lines(errors),
        "",
    ]

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
            "explanation.txt:",
            explanation.strip(),
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
    explanation = (case_dir / "explanation.txt").read_text(encoding="utf-8")
    out_path = case_dir / "scene_draft.json"
    errors_path = case_dir / "llm2_validation_errors.txt"

    enums = load_enums()
    allowed_object_types = set(enums["object_types"])
    prompt = load_prompt("llm2_scene_draft.md")
    teaching_plan_path = case_dir / "teaching_plan.json"
    teaching_plan = None
    if teaching_plan_path.exists():
        try:
            teaching_plan = json.loads(teaching_plan_path.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            teaching_plan = None

    user_payload = _build_user_payload(
        problem=problem,
        explanation=explanation,
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
                explanation=explanation,
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
