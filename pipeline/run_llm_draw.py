from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from components.physics.specs import PHYSICS_OBJECT_PARAM_SPECS
from pipeline.config import load_enums
from pipeline.env import load_dotenv
from pipeline.json_utils import load_json_from_llm
from pipeline.llm.types import ChatMessage
from pipeline.llm.zhipu import chat_completion, load_zhipu_config, load_zhipu_stage_config
from pipeline.llm_continuation import continue_json_output
from pipeline.prompting import compose_prompt, load_prompt
from pipeline.run_llm2 import _compact_narrative_plan, _compact_teaching_plan
from schema.scene_draw_models import SceneDrawPlan
from schema.scene_semantic_models import SceneSemanticPlan

_PART_REF_KEYS: tuple[str, ...] = (
    "part_id",
    "part_a",
    "part_b",
    "from_part_id",
    "to_part_id",
    "source_part_id",
    "target_part_id",
)
_TRACK_REF_KEYS: tuple[str, ...] = ("track_id", "source_track_id", "target_track_id")
_ALLOWED_CONSTRAINT_TYPES: set[str] = {"attach", "midpoint", "distance", "on_track_pose"}


def _write_continuation_chunks(case_dir: Path, stem: str, chunks: list[str]) -> None:
    for idx, chunk in enumerate(chunks, start=1):
        (case_dir / f"{stem}_{idx}.txt").write_text(chunk.strip() + "\n", encoding="utf-8")


def _render_error_lines(errors: list[str], *, limit: int = 60) -> str:
    if not errors:
        return "(no validation errors)"
    lines = [f"- {err}" for err in errors[:limit]]
    if len(errors) > limit:
        lines.append(f"- ... and {len(errors) - limit} more errors")
    return "\n".join(lines)


def _semantic_composite_targets(semantic: SceneSemanticPlan) -> dict[str, list[str]]:
    targets: dict[str, list[str]] = {}
    for scene in semantic.scenes:
        object_ids = [obj.id for obj in scene.objects if obj.type == "CompositeObject"]
        targets[scene.id] = object_ids
    return targets


def _load_anchor_dictionary() -> dict[str, list[str]]:
    path = Path(__file__).resolve().parents[1] / "llm_constraints" / "specs" / "anchors_dictionary.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}

    components = payload.get("components")
    if not isinstance(components, dict):
        return {}

    result: dict[str, list[str]] = {}
    for comp_type, comp_payload in components.items():
        if not isinstance(comp_type, str) or not isinstance(comp_payload, dict):
            continue
        anchors_raw = comp_payload.get("anchors")
        if not isinstance(anchors_raw, list):
            continue
        anchors = [str(item).strip() for item in anchors_raw if str(item).strip()]
        if anchors:
            result[comp_type] = anchors
    return result


def _build_component_contract(*, allowed_part_types: list[str]) -> dict[str, dict[str, list[str]]]:
    anchors_by_type = _load_anchor_dictionary()
    contract: dict[str, dict[str, list[str]]] = {}
    for part_type in sorted(set(allowed_part_types)):
        params = list(PHYSICS_OBJECT_PARAM_SPECS.get(part_type, ()))
        anchors = list(anchors_by_type.get(part_type, []))
        contract[part_type] = {
            "params": params,
            "anchors": anchors,
        }
    return contract


def _load_constraint_specs() -> dict[str, Any]:
    path = Path(__file__).resolve().parents[1] / "llm_constraints" / "specs" / "constraints_whitelist.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}
    constraints = payload.get("constraints")
    return constraints if isinstance(constraints, dict) else {}


def _build_constraint_contract() -> dict[str, dict[str, Any]]:
    specs = _load_constraint_specs()
    contract: dict[str, dict[str, Any]] = {}
    for ctype in sorted(_ALLOWED_CONSTRAINT_TYPES):
        raw_spec = specs.get(ctype)
        if not isinstance(raw_spec, dict):
            contract[ctype] = {"args": {}, "required_any_of": []}
            continue

        raw_args = raw_spec.get("args")
        args: dict[str, Any] = {}
        if isinstance(raw_args, dict):
            for key in sorted(raw_args.keys()):
                key_text = str(key).strip()
                if not key_text:
                    continue
                rule = raw_args.get(key)
                if isinstance(rule, dict):
                    args[key_text] = dict(rule)
                else:
                    args[key_text] = {"type": str(rule).strip() if rule is not None else ""}

        raw_required = raw_spec.get("required_any_of")
        required_any_of: list[list[str]] = []
        if isinstance(raw_required, list):
            for group in raw_required:
                if isinstance(group, list):
                    items = [str(item).strip() for item in group if str(item).strip()]
                    if items:
                        required_any_of.append(items)

        entry: dict[str, Any] = {
            "args": args,
            "required_any_of": required_any_of,
        }
        extra_rule = raw_spec.get("extra_rule")
        if isinstance(extra_rule, str) and extra_rule.strip():
            entry["extra_rule"] = extra_rule.strip()
        contract[ctype] = entry
    return contract


def _to_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _iter_ref_values(args: dict[str, Any], key: str) -> list[str]:
    value = args.get(key)
    if isinstance(value, str):
        item = value.strip()
        return [item] if item else []
    if isinstance(value, list):
        result: list[str] = []
        for item in value:
            if isinstance(item, str):
                text = item.strip()
                if text:
                    result.append(text)
        return result
    return []


def _args_reference_unknown(*, args: dict[str, Any], part_ids: set[str], track_ids: set[str]) -> bool:
    for key in _PART_REF_KEYS:
        for part_id in _iter_ref_values(args, key):
            if part_id not in part_ids:
                return True
    for key in _TRACK_REF_KEYS:
        for track_id in _iter_ref_values(args, key):
            if track_id not in track_ids:
                return True
    return False


def _normalize_seed_pose(seed_pose: Any) -> dict[str, Any] | None:
    if not isinstance(seed_pose, dict):
        return None

    raw = dict(seed_pose)
    position = raw.get("position")
    if isinstance(position, (list, tuple)):
        if len(position) >= 1 and "x" not in raw:
            x = _to_float(position[0])
            if x is not None:
                raw["x"] = x
        if len(position) >= 2 and "y" not in raw:
            y = _to_float(position[1])
            if y is not None:
                raw["y"] = y
        if len(position) >= 3 and "z" not in raw:
            z = _to_float(position[2])
            if z is not None:
                raw["z"] = z

    if "rotation" in raw and "theta" not in raw:
        theta = _to_float(raw.get("rotation"))
        if theta is not None:
            raw["theta"] = theta

    normalized: dict[str, Any] = {}
    for key in ("x", "y", "theta", "scale", "z"):
        if key not in raw:
            continue
        value = _to_float(raw.get(key))
        if value is None:
            continue
        if key == "scale" and value <= 0:
            value = 1.0
        normalized[key] = value

    return normalized or None


def _normalize_graph(graph: Any) -> dict[str, Any]:
    if not isinstance(graph, dict):
        return {"version": "0.1", "space": {}, "parts": [], "tracks": [], "constraints": [], "motions": []}

    result = dict(graph)
    if not isinstance(result.get("space"), dict):
        result["space"] = {}

    raw_parts = result.get("parts")
    parts: list[dict[str, Any]] = []
    if isinstance(raw_parts, list):
        for item in raw_parts:
            if not isinstance(item, dict):
                continue
            part = dict(item)
            part.pop("anchors", None)
            seed = _normalize_seed_pose(part.get("seed_pose"))
            if seed is None:
                part.pop("seed_pose", None)
            else:
                part["seed_pose"] = seed
            parts.append(part)
    result["parts"] = parts
    part_ids = {str(part.get("id", "")).strip() for part in parts if str(part.get("id", "")).strip()}

    raw_tracks = result.get("tracks")
    tracks: list[dict[str, Any]] = []
    if isinstance(raw_tracks, list):
        for item in raw_tracks:
            if not isinstance(item, dict):
                continue
            track = dict(item)
            tracks.append(track)
    result["tracks"] = tracks
    track_ids = {str(track.get("id", "")).strip() for track in tracks if str(track.get("id", "")).strip()}

    raw_constraints = result.get("constraints")
    constraints: list[dict[str, Any]] = []
    if isinstance(raw_constraints, list):
        for item in raw_constraints:
            if not isinstance(item, dict):
                continue
            constraint = dict(item)
            if "args" not in constraint and isinstance(constraint.get("params"), dict):
                constraint["args"] = dict(constraint.pop("params"))
            elif "args" in constraint and "params" in constraint:
                constraint.pop("params", None)

            ctype = str(constraint.get("type", "")).strip()
            if ctype not in _ALLOWED_CONSTRAINT_TYPES:
                continue

            args = constraint.get("args")
            if not isinstance(args, dict):
                args = {}
            if _args_reference_unknown(args=args, part_ids=part_ids, track_ids=track_ids):
                continue
            if ctype == "on_track_pose":
                side_raw = args.get("contact_side")
                if side_raw is not None:
                    side = str(side_raw).strip().lower()
                    if side not in {"outer", "inner"}:
                        args["contact_side"] = "outer"
                # Global policy: clearance is removed from project and must not appear.
                args.pop("clearance", None)

            constraint["args"] = args
            constraints.append(constraint)
    result["constraints"] = constraints

    raw_motions = result.get("motions")
    motions: list[dict[str, Any]] = []
    if isinstance(raw_motions, list):
        for item in raw_motions:
            if not isinstance(item, dict):
                continue
            motion = dict(item)
            if "args" not in motion and isinstance(motion.get("params"), dict):
                motion["args"] = dict(motion.pop("params"))
            elif "args" in motion and "params" in motion:
                motion.pop("params", None)

            args = motion.get("args")
            if not isinstance(args, dict):
                args = {}
            if _args_reference_unknown(args=args, part_ids=part_ids, track_ids=track_ids):
                continue
            # Global policy: clearance is removed from project and must not appear.
            args.pop("clearance", None)
            segments = args.get("segments")
            if isinstance(segments, list):
                for segment in segments:
                    if isinstance(segment, dict):
                        segment.pop("clearance", None)

            timeline = motion.get("timeline")
            if not isinstance(timeline, list):
                motion["timeline"] = []
            motion["args"] = args
            motions.append(motion)
    result["motions"] = motions

    return result


def _normalize_draw_payload(data: Any) -> Any:
    if not isinstance(data, dict):
        return data

    result = dict(data)
    raw_scenes = result.get("scenes")
    if not isinstance(raw_scenes, list):
        return result

    scenes: list[dict[str, Any]] = []
    for scene in raw_scenes:
        if not isinstance(scene, dict):
            continue
        scene_item = dict(scene)
        raw_composites = scene_item.get("composites")
        if isinstance(raw_composites, list):
            composites: list[dict[str, Any]] = []
            for item in raw_composites:
                if not isinstance(item, dict):
                    continue
                composite = dict(item)
                composite["graph"] = _normalize_graph(composite.get("graph"))
                composites.append(composite)
            scene_item["composites"] = composites
        scenes.append(scene_item)
    result["scenes"] = scenes
    return result


def _validate_draw_against_semantic(*, draw: SceneDrawPlan, semantic: SceneSemanticPlan) -> list[str]:
    errors: list[str] = []
    semantic_scene_by_id = {scene.id: scene for scene in semantic.scenes}
    draw_scene_by_id = {scene.id: scene for scene in draw.scenes}

    for scene_id, scene in semantic_scene_by_id.items():
        composite_ids = [obj.id for obj in scene.objects if obj.type == "CompositeObject"]
        draw_scene = draw_scene_by_id.get(scene_id)
        if not composite_ids:
            continue
        if draw_scene is None:
            errors.append(f"scene_draw missing scene id: {scene_id}")
            continue

        draw_ids = {item.object_id for item in draw_scene.composites}
        for object_id in composite_ids:
            if object_id not in draw_ids:
                errors.append(f"scene '{scene_id}' missing composite graph for object '{object_id}'")

        valid_ids = {obj.id for obj in scene.objects}
        for object_id in draw_ids:
            if object_id not in valid_ids:
                errors.append(f"scene '{scene_id}' draw contains unknown object id: {object_id}")
                continue
            otype = next((obj.type for obj in scene.objects if obj.id == object_id), "")
            if otype != "CompositeObject":
                errors.append(f"scene '{scene_id}' object '{object_id}' is not CompositeObject")

    for scene in draw.scenes:
        if scene.id not in semantic_scene_by_id:
            errors.append(f"scene_draw contains extra scene id not in scene_semantic: {scene.id}")

    return errors


def _validate_graph_region_isolation(*, draw: SceneDrawPlan) -> list[str]:
    errors: list[str] = []

    for scene in draw.scenes:
        for composite in scene.composites:
            part_ids = {part.id for part in composite.graph.parts}
            for track in composite.graph.tracks:
                data = dict(track.data or {})
                space_raw = data.get("space", "local")
                space = str(space_raw).strip().lower() if space_raw is not None else "local"
                if space == "world":
                    continue

                # Local tracks are interpreted in this composite graph's coordinate context.
                # They must explicitly bind to a local part and cannot reference other composites.
                part_id_raw = data.get("part_id")
                part_id = str(part_id_raw).strip() if isinstance(part_id_raw, str) else ""
                if not part_id:
                    errors.append(
                        f"scene '{scene.id}' composite '{composite.object_id}' track '{track.id}' "
                        "local track requires data.part_id"
                    )
                    continue
                if part_id not in part_ids:
                    errors.append(
                        f"scene '{scene.id}' composite '{composite.object_id}' track '{track.id}' "
                        f"data.part_id references unknown local part id: {part_id}"
                    )

    return errors


def _validate_track_motion_policy(*, draw: SceneDrawPlan) -> list[str]:
    errors: list[str] = []

    for scene in draw.scenes:
        for composite in scene.composites:
            graph = composite.graph
            track_type_by_id = {track.id: str(track.type).strip().lower() for track in graph.tracks}

            for track_index, track in enumerate(graph.tracks):
                ttype = str(track.type).strip().lower()
                path = (
                    f"scene '{scene.id}' composite '{composite.object_id}' "
                    f"tracks[{track_index}] ({track.id})"
                )
                if ttype == "line":
                    errors.append(f"{path} type=line is forbidden; use segment or arc")
                elif ttype not in {"segment", "arc"}:
                    errors.append(f"{path} unsupported type: {ttype}")
                    continue

                data = dict(track.data or {})
                space_raw = data.get("space", "")
                space = str(space_raw).strip().lower() if isinstance(space_raw, str) else ""
                if space and space not in {"local", "world"}:
                    errors.append(f"{path} data.space must be 'local' or 'world'")
                    continue

                if ttype == "segment":
                    allowed_segment_keys = {"space", "part_id", "anchor_a", "anchor_b", "x1", "y1", "x2", "y2"}
                    unknown = sorted(key for key in data.keys() if key not in allowed_segment_keys)
                    if unknown:
                        errors.append(f"{path} segment data has unknown keys: {', '.join(unknown)}")
                    effective_space = space or ("world" if all(_to_float(data.get(k)) is not None for k in ("x1", "y1", "x2", "y2")) else "local")
                    if effective_space == "local":
                        part_id = str(data.get("part_id", "")).strip()
                        anchor_a = str(data.get("anchor_a", "")).strip()
                        anchor_b = str(data.get("anchor_b", "")).strip()
                        if not part_id:
                            errors.append(f"{path} local segment requires data.part_id")
                        if not anchor_a or not anchor_b:
                            errors.append(f"{path} local segment requires data.anchor_a and data.anchor_b")
                        if any(key in data for key in ("x1", "y1", "x2", "y2")):
                            errors.append(f"{path} local segment forbids x1/y1/x2/y2")
                    else:
                        for key in ("x1", "y1", "x2", "y2"):
                            if _to_float(data.get(key)) is None:
                                errors.append(f"{path} world segment requires numeric {key}")
                        forbidden_local = [key for key in ("part_id", "anchor_a", "anchor_b") if key in data]
                        if forbidden_local:
                            errors.append(
                                f"{path} world segment forbids local keys: {', '.join(forbidden_local)}"
                            )

                if ttype == "arc":
                    allowed_arc_keys = {"space", "part_id", "center", "cx", "cy", "radius", "start", "end"}
                    unknown = sorted(key for key in data.keys() if key not in allowed_arc_keys)
                    if unknown:
                        errors.append(f"{path} arc data has unknown keys: {', '.join(unknown)}")
                    if not space:
                        errors.append(f"{path} arc track requires explicit data.space")
                        continue
                    if "center" in data and not (isinstance(data.get("center"), str) and str(data.get("center")).strip()):
                        errors.append(f"{path} arc data.center must be non-empty anchor name string")
                    for key in ("radius", "start", "end"):
                        if _to_float(data.get(key)) is None:
                            errors.append(f"{path} arc data requires numeric {key}")
                    if space == "local":
                        part_id = str(data.get("part_id", "")).strip()
                        if not part_id:
                            errors.append(f"{path} local arc requires data.part_id")
                        has_center_anchor = isinstance(data.get("center"), str) and bool(str(data.get("center")).strip())
                        has_center_xy = _to_float(data.get("cx")) is not None and _to_float(data.get("cy")) is not None
                        if not (has_center_anchor or has_center_xy):
                            errors.append(f"{path} local arc requires center or cx/cy")
                    else:
                        if _to_float(data.get("cx")) is None or _to_float(data.get("cy")) is None:
                            errors.append(f"{path} world arc requires numeric cx/cy")
                        forbidden_local = [key for key in ("part_id", "center") if key in data]
                        if forbidden_local:
                            errors.append(
                                f"{path} world arc forbids local keys: {', '.join(forbidden_local)}"
                            )

            for constraint_index, constraint in enumerate(graph.constraints):
                if str(constraint.type).strip() != "on_track_pose":
                    continue
                args = dict(constraint.args or {})
                track_id = str(args.get("track_id", "")).strip()
                if not track_id or track_type_by_id.get(track_id) not in {"segment", "arc"}:
                    continue
                value = _to_float(args.get("s", args.get("t")))
                path = (
                    f"scene '{scene.id}' composite '{composite.object_id}' "
                    f"constraints[{constraint_index}] ({constraint.id})"
                )
                if value is None:
                    errors.append(f"{path} on_track_pose requires numeric s/t for segment/arc")
                    continue
                if value < 0.0 or value > 1.0:
                    errors.append(f"{path} on_track_pose s out of range [0,1]: {value}")

            for motion_index, motion in enumerate(graph.motions):
                mtype = str(motion.type).strip()
                args = dict(motion.args or {})
                path = (
                    f"scene '{scene.id}' composite '{composite.object_id}' "
                    f"motions[{motion_index}] ({motion.id})"
                )

                if mtype == "on_track":
                    track_id = str(args.get("track_id", "")).strip()
                    if not track_id:
                        errors.append(f"{path} on_track requires args.track_id")
                        continue
                    if track_type_by_id.get(track_id) not in {"segment", "arc"}:
                        errors.append(f"{path} on_track track_id '{track_id}' must reference segment/arc")
                        continue
                    param_key = str(args.get("param_key", "s")).strip() or "s"
                    for point_index, point in enumerate(motion.timeline):
                        if not isinstance(point, dict):
                            continue
                        value = _to_float(point.get(param_key))
                        if value is None:
                            errors.append(f"{path} timeline[{point_index}].{param_key} must be numeric")
                            continue
                        if value < 0.0 or value > 1.0:
                            errors.append(f"{path} timeline[{point_index}].{param_key} out of range [0,1]: {value}")
                    continue

                if mtype != "on_track_schedule":
                    continue

                segments = args.get("segments")
                if not isinstance(segments, list) or not segments:
                    errors.append(f"{path} on_track_schedule requires args.segments")
                    continue

                prev_u1: float | None = None
                for segment_index, segment in enumerate(segments):
                    if not isinstance(segment, dict):
                        continue
                    seg_path = f"{path} segments[{segment_index}]"
                    track_id = str(segment.get("track_id", "")).strip()
                    if not track_id:
                        errors.append(f"{seg_path} requires track_id")
                    elif track_type_by_id.get(track_id) not in {"segment", "arc"}:
                        errors.append(f"{seg_path} track_id '{track_id}' must reference segment/arc")

                    s0 = _to_float(segment.get("s0", segment.get("from_s")))
                    s1 = _to_float(segment.get("s1", segment.get("to_s")))
                    if s0 is None or s1 is None:
                        errors.append(f"{seg_path} requires numeric s0/s1 (or from_s/to_s)")
                    else:
                        if s0 < 0.0 or s0 > 1.0:
                            errors.append(f"{seg_path}.s0 out of range [0,1]: {s0}")
                        if s1 < 0.0 or s1 > 1.0:
                            errors.append(f"{seg_path}.s1 out of range [0,1]: {s1}")

                    u0 = _to_float(segment.get("u0", segment.get("from_u")))
                    u1 = _to_float(segment.get("u1", segment.get("to_u")))
                    if u0 is None or u1 is None:
                        errors.append(f"{seg_path} requires numeric u0/u1 (or from_u/to_u)")
                    else:
                        if u1 <= u0:
                            errors.append(f"{seg_path} requires u1 > u0")
                        if prev_u1 is not None and abs(u0 - prev_u1) > 1e-6:
                            errors.append(f"{seg_path}.u0 must equal previous segment.u1 (continuous schedule)")
                        prev_u1 = u1

    return errors


def _build_user_payload(
    *,
    problem: str,
    teaching_plan: dict[str, Any] | None,
    narrative_plan: dict[str, Any] | None,
    semantic: SceneSemanticPlan,
    allowed_part_types: list[str],
    component_contract: dict[str, dict[str, list[str]]],
    constraint_contract: dict[str, dict[str, Any]],
) -> str:
    compact_teaching = _compact_teaching_plan(teaching_plan)
    compact_narrative = _compact_narrative_plan(narrative_plan)
    targets = _semantic_composite_targets(semantic)

    lines = [
        "题目：",
        problem.strip(),
        "",
        "输出要求：",
        "- 输出 scene_draw.json（仅负责 CompositeObject 的 graph）。",
        "- 只输出一个严格 JSON 对象，不要 markdown。",
        "- scene_draw.scenes[].id 必须与 scene_semantic 对齐。",
        "- scene_draw.composites[].object_id 必须是该 scene 的 CompositeObject。",
        "- 一个 CompositeObject 对应一个区域 graph；跨区域禁止共享 part_id/track_id 引用。",
        "- local track 的 data.part_id 必须引用当前 composite.graph.parts 内部 part。",
        "- 坐标格式硬约束：组件坐标只用 [x,y]/[x,y,z]；轨道数值坐标只用 x1/y1/x2/y2、cx/cy；局部圆心锚点只用字符串 center。",
        "",
        "允许的 CompositeObject part.type：",
        json.dumps(allowed_part_types, ensure_ascii=False),
        "",
        "组件参数与锚点合同（已注入，必须严格遵守）：",
        json.dumps(component_contract, ensure_ascii=False, indent=2),
        "",
        "约束参数合同（已注入，constraints[].type 与 args 必须严格遵守）：",
        json.dumps(constraint_contract, ensure_ascii=False, indent=2),
        "",
        "本次必须绘制的 CompositeObject 目标：",
        json.dumps(targets, ensure_ascii=False, indent=2),
        "重要：上面 targets 是不可变白名单。只能为这些 object_id 生成 graph，禁止新增/删除/改名。",
        "重要：llm_draw 只负责画图，不得改 scene 结构与对象语义。",
        "",
        "scene_semantic.json：",
        json.dumps(semantic.model_dump(mode="json"), ensure_ascii=False, indent=2),
    ]

    if compact_teaching is not None:
        lines.extend(
            [
                "",
                "teaching_plan（用于物理量一致性）：",
                json.dumps(compact_teaching, ensure_ascii=False, indent=2),
            ]
        )

    if compact_narrative is not None:
        lines.extend(
            [
                "",
                "narrative_plan（用于过程节奏与阶段划分）：",
                json.dumps(compact_narrative, ensure_ascii=False, indent=2),
            ]
        )

    return "\n".join(lines)


def _build_repair_payload(
    *,
    problem: str,
    semantic: SceneSemanticPlan,
    component_contract: dict[str, dict[str, list[str]]],
    constraint_contract: dict[str, dict[str, Any]],
    raw_content: str,
    errors: list[str],
    round_index: int,
) -> str:
    targets = _semantic_composite_targets(semantic)
    return "\n".join(
        [
            f"这是第 {round_index} 轮修复。请在最小改动下修复 scene_draw.json。",
            "只输出 JSON。",
            "",
            "校验错误：",
            _render_error_lines(errors),
            "",
            "题目：",
            problem.strip(),
            "",
            "必须绘制目标：",
            json.dumps(targets, ensure_ascii=False, indent=2),
            "重要：targets 是不可变白名单。禁止新增/删除/改名 object_id。",
            "",
            "scene_semantic.json：",
            json.dumps(semantic.model_dump(mode="json"), ensure_ascii=False, indent=2),
            "",
            "组件参数与锚点合同（已注入，修复时必须严格遵守）：",
            json.dumps(component_contract, ensure_ascii=False, indent=2),
            "",
            "约束参数合同（已注入，修复时必须严格遵守）：",
            json.dumps(constraint_contract, ensure_ascii=False, indent=2),
            "",
            "当前错误内容：",
            raw_content.strip(),
            "",
            "硬约束：",
            "1) 仅输出 scene_draw.json。",
            "2) 每个 composite 必须给出完整 graph：space/parts/tracks/constraints/motions。",
            "3) 动态过程必须给 graph.motions（不能只给静态图）。",
            "4) 不得输出 scene_semantic 中不存在的 scene/object。",
            "5) 一个 CompositeObject 对应一个区域 graph，禁止跨 composite 引用 part/track。",
            "6) local track 必须写 data.part_id，且该 part_id 必须在本 composite.graph.parts 内。",
            "7) part.params 只能使用上方合同中该 part.type 的 params。",
            "8) 任何 anchor 字段只能使用上方合同中该 part.type 的 anchors。",
            "9) constraints[].args 只能使用上方约束合同中该 constraint.type 的 args。",
            "10) line 轨道一律不通过；segment/arc 轨道的 s 越界也不通过：on_track.timeline.s 与 on_track_schedule.segments.s0/s1 必须都在 [0,1]。",
            "11) 坐标格式硬约束：组件坐标只用 [x,y]/[x,y,z]；轨道数值坐标只用 x1/y1/x2/y2、cx/cy；局部圆心锚点只用字符串 center。",
            "12) 禁止所有历史别名：p1/p2、p1_local/x1_local、a1/a2、center:{x,y}。",
            "",
            "只输出修复后的 JSON。",
        ]
    )


def _parse_and_validate(
    *,
    content: str,
    semantic: SceneSemanticPlan,
) -> tuple[dict[str, Any] | None, list[str]]:
    try:
        data = load_json_from_llm(content)
    except Exception as exc:  # noqa: BLE001
        return None, [f"JSON parse failed: {exc}"]

    normalized = _normalize_draw_payload(data)

    try:
        draw = SceneDrawPlan.model_validate(normalized)
    except Exception as exc:  # noqa: BLE001
        return None, [f"scene_draw schema invalid: {exc}"]

    semantic_errors = _validate_draw_against_semantic(draw=draw, semantic=semantic)
    if semantic_errors:
        return None, semantic_errors
    region_errors = _validate_graph_region_isolation(draw=draw)
    if region_errors:
        return None, region_errors
    policy_errors = _validate_track_motion_policy(draw=draw)
    if policy_errors:
        return None, policy_errors
    return draw.model_dump(mode="json"), []


def main() -> int:
    parser = argparse.ArgumentParser(description="LLM-draw: generate scene_draw.json")
    parser.add_argument("--case", default="cases/demo_001", help="Case directory, e.g. cases/demo_001")
    parser.add_argument("--problem", default=None, help="Optional problem file path (default: case/problem.md)")
    parser.add_argument(
        "--semantic",
        default=None,
        help="Optional scene_semantic.json path (default: case/scene_semantic.json)",
    )
    parser.add_argument(
        "--teaching-plan",
        default=None,
        help="Optional teaching_plan.json path (default: case/teaching_plan.json)",
    )
    parser.add_argument(
        "--narrative-plan",
        default=None,
        help="Optional narrative_plan.json path (default: case/narrative_plan.json if exists)",
    )
    parser.add_argument("--no-repair", action="store_true", help="Skip repair when parse/validation fails")
    parser.add_argument("--continue-rounds", type=int, default=2, help="Max continuation rounds for truncated JSON")
    parser.add_argument("--repair-rounds", type=int, default=2, help="Max validation-driven repair rounds")
    args = parser.parse_args()

    load_dotenv()
    base_llm_cfg = load_zhipu_config()
    generate_llm_cfg = load_zhipu_stage_config("llm_draw", "generate", base_cfg=base_llm_cfg)
    continue_llm_cfg = load_zhipu_stage_config("llm_draw", "continue", base_cfg=base_llm_cfg)
    repair_llm_cfg = load_zhipu_stage_config("llm_draw", "repair", base_cfg=base_llm_cfg)

    case_dir = Path(args.case)
    problem_path = Path(args.problem) if args.problem else (case_dir / "problem.md")
    semantic_path = Path(args.semantic) if args.semantic else (case_dir / "scene_semantic.json")
    teaching_plan_path = Path(args.teaching_plan) if args.teaching_plan else (case_dir / "teaching_plan.json")
    narrative_plan_path = Path(args.narrative_plan) if args.narrative_plan else (case_dir / "narrative_plan.json")
    out_path = case_dir / "scene_draw.json"

    # Avoid stale draw outputs causing semantic/draw mismatch confusion in downstream merge steps.
    if out_path.exists():
        out_path.unlink()

    problem = problem_path.read_text(encoding="utf-8")
    semantic = SceneSemanticPlan.model_validate(json.loads(semantic_path.read_text(encoding="utf-8")))

    teaching_plan: dict[str, Any] | None = None
    if teaching_plan_path.exists():
        parsed = json.loads(teaching_plan_path.read_text(encoding="utf-8"))
        if isinstance(parsed, dict):
            teaching_plan = parsed
    elif args.teaching_plan:
        print(f"Missing specified teaching plan file: {teaching_plan_path}", file=sys.stderr)
        return 2

    narrative_plan: dict[str, Any] | None = None
    if narrative_plan_path.exists():
        parsed = json.loads(narrative_plan_path.read_text(encoding="utf-8"))
        if isinstance(parsed, dict):
            narrative_plan = parsed
    elif args.narrative_plan:
        print(f"Missing specified narrative plan file: {narrative_plan_path}", file=sys.stderr)
        return 2

    enums = load_enums()
    allowed_object_types = set(enums["object_types"])
    top_level = {"TextBlock", "BulletPanel", "Formula", "CompositeObject", "CustomObject"}
    allowed_part_types = sorted(t for t in allowed_object_types if t not in top_level)
    component_contract = _build_component_contract(allowed_part_types=allowed_part_types)
    constraint_contract = _build_constraint_contract()

    prompt = compose_prompt("llm_draw", context={"has_narrative_plan": narrative_plan is not None})
    system_prompt_path = case_dir / "llm_draw_system_prompt.txt"
    system_prompt_path.write_text(prompt.strip() + "\n", encoding="utf-8")

    user_payload = _build_user_payload(
        problem=problem,
        teaching_plan=teaching_plan,
        narrative_plan=narrative_plan,
        semantic=semantic,
        allowed_part_types=allowed_part_types,
        component_contract=component_contract,
        constraint_contract=constraint_contract,
    )
    content = chat_completion(
        [ChatMessage(role="system", content=prompt), ChatMessage(role="user", content=user_payload)],
        cfg=generate_llm_cfg,
    )
    content, cont_chunks = continue_json_output(
        content,
        system_prompt=prompt,
        user_payload=user_payload,
        parse_fn=load_json_from_llm,
        max_rounds=args.continue_rounds,
        llm_cfg=continue_llm_cfg,
    )

    raw_path = case_dir / "llm_draw_raw.txt"
    raw_path.write_text(content.strip() + "\n", encoding="utf-8")
    _write_continuation_chunks(case_dir, "llm_draw_continue_raw", cont_chunks)

    validation_log: list[str] = []
    data, errors = _parse_and_validate(content=content, semantic=semantic)
    if errors:
        validation_log.append("[initial]")
        validation_log.extend(errors)
        validation_log.append("")

    errors_path = case_dir / "llm_draw_validation_errors.txt"
    if errors and args.no_repair:
        errors_path.write_text("\n".join(validation_log).strip() + "\n", encoding="utf-8")
        print(f"LLM-draw output invalid. See: {raw_path} and {errors_path}", file=sys.stderr)
        return 2

    if errors:
        repair_prompt = load_prompt("json_repair.md")
        current_content = content
        repair_raw_path = case_dir / "llm_draw_repair_raw.txt"
        for round_index in range(1, max(1, args.repair_rounds) + 1):
            repair_payload = _build_repair_payload(
                problem=problem,
                semantic=semantic,
                component_contract=component_contract,
                constraint_contract=constraint_contract,
                raw_content=current_content,
                errors=errors,
                round_index=round_index,
            )
            repaired = chat_completion(
                [ChatMessage(role="system", content=repair_prompt), ChatMessage(role="user", content=repair_payload)],
                cfg=repair_llm_cfg,
            )
            repaired, repair_cont_chunks = continue_json_output(
                repaired,
                system_prompt=repair_prompt,
                user_payload=repair_payload,
                parse_fn=load_json_from_llm,
                max_rounds=args.continue_rounds,
                llm_cfg=continue_llm_cfg,
            )
            repair_raw_path.write_text(repaired.strip() + "\n", encoding="utf-8")
            (case_dir / f"llm_draw_repair_raw_round_{round_index}.txt").write_text(
                repaired.strip() + "\n", encoding="utf-8"
            )
            _write_continuation_chunks(case_dir, f"llm_draw_repair_continue_raw_r{round_index}", repair_cont_chunks)

            data, errors = _parse_and_validate(content=repaired, semantic=semantic)
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
                "LLM-draw repair rounds finished but output is still invalid. "
                f"See: {raw_path}, {repair_raw_path}, {errors_path}",
                file=sys.stderr,
            )
            return 2

    assert data is not None
    if errors_path.exists():
        errors_path.unlink()

    out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(str(out_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

