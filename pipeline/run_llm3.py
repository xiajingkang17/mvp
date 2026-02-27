from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from pipeline.config import load_enums
from pipeline.env import load_dotenv
from pipeline.json_utils import load_json_from_llm
from pipeline.llm.types import ChatMessage
from pipeline.llm.zhipu import chat_completion, load_zhipu_config, load_zhipu_stage_config
from pipeline.llm_continuation import continue_json_output
from pipeline.prompting import compose_prompt, load_prompt


_ALLOWED_PLACEMENT_ANCHORS = {"C", "U", "D", "L", "R", "UL", "UR", "DL", "DR"}


def _write_continuation_chunks(case_dir: Path, stem: str, chunks: list[str]) -> None:
    for idx, chunk in enumerate(chunks, start=1):
        (case_dir / f"{stem}_{idx}.txt").write_text(chunk.strip() + "\n", encoding="utf-8")


def _layout_strategy_hints() -> dict[str, Any]:
    return {
        "layout_type": "always use layout.type = free",
        "placement_schema": {
            "cx": "float in [0,1], normalized x in safe area",
            "cy": "float in [0,1], normalized y in safe area",
            "w": "float in (0,1], normalized width in safe area",
            "h": "float in (0,1], normalized height in safe area",
            "anchor": "one of C/U/D/L/R/UL/UR/DL/DR",
        },
        "composition_examples": [
            "diagram + equation: diagram at (0.32,0.56,w=0.58,h=0.82), equation at (0.76,0.60,w=0.40,h=0.42)",
            "equation + conclusion text: equation upper-middle, conclusion lower-middle, keep center lane clear",
            "single hero object: centered wide hero, secondary text in corner with smaller area",
        ],
        "readability": [
            "Keep one visual focus per scene.",
            "Avoid overlap between objects (unless intentional callout).",
            "Respect reading flow from focus object to supporting objects.",
            "Reserve visual breathing room around conclusion/check text.",
        ],
    }


def _scene_role_summary(draft: dict) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    for scene in draft.get("scenes") or []:
        scene_id = scene.get("id")
        roles = scene.get("roles")
        if isinstance(scene_id, str) and isinstance(roles, dict):
            compact: dict[str, str] = {}
            for k, v in roles.items():
                key = str(k).strip()
                value = str(v).strip()
                if key and value:
                    compact[key] = value
            if compact:
                result[scene_id] = compact
    return result


def _scene_object_catalog(draft: dict) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for scene in draft.get("scenes") or []:
        scene_id = scene.get("id")
        objects = scene.get("objects")
        if not isinstance(scene_id, str) or not isinstance(objects, list):
            continue
        ids: list[str] = []
        seen: set[str] = set()
        for obj in objects:
            if not isinstance(obj, dict):
                continue
            object_id = str(obj.get("id", "")).strip()
            if object_id and object_id not in seen:
                seen.add(object_id)
                ids.append(object_id)
        result[scene_id] = ids
    return result


def _global_object_ids(draft: dict) -> set[str]:
    ids: set[str] = set()
    for object_ids in _scene_object_catalog(draft).values():
        ids.update(object_ids)
    return ids


def _draft_scene_ids(draft: dict) -> list[str]:
    ids: list[str] = []
    seen: set[str] = set()
    for scene in draft.get("scenes") or []:
        scene_id = str(scene.get("id", "")).strip()
        if scene_id and scene_id not in seen:
            seen.add(scene_id)
            ids.append(scene_id)
    return ids


def _safe_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _motion_timeline_span(motion: Any) -> float:
    if not isinstance(motion, dict):
        return 0.0
    timeline = motion.get("timeline")
    if not isinstance(timeline, list):
        return 0.0
    points: list[float] = []
    for item in timeline:
        if not isinstance(item, dict):
            continue
        t_val = _safe_float(item.get("t"))
        if t_val is None:
            continue
        points.append(t_val)
    if len(points) < 2:
        return 0.0
    return max(points) - min(points)


def _scene_motion_span_map(draft: dict) -> dict[str, float]:
    result: dict[str, float] = {}
    scenes = draft.get("scenes")
    if not isinstance(scenes, list):
        return result
    for scene in scenes:
        if not isinstance(scene, dict):
            continue
        scene_id = str(scene.get("id", "")).strip()
        if not scene_id:
            continue
        max_span = 0.0
        objects = scene.get("objects")
        if not isinstance(objects, list):
            result[scene_id] = 0.0
            continue
        for obj in objects:
            if not isinstance(obj, dict):
                continue
            if str(obj.get("type", "")).strip() != "CompositeObject":
                continue
            params = obj.get("params")
            if not isinstance(params, dict):
                continue
            graph = params.get("graph")
            if not isinstance(graph, dict):
                continue
            motions = graph.get("motions")
            if not isinstance(motions, list):
                continue
            for motion in motions:
                span = _motion_timeline_span(motion)
                if span > max_span:
                    max_span = span
        result[scene_id] = max_span
    return result


def _compact_narrative_plan(narrative_plan: Any) -> dict[str, Any] | None:
    if not isinstance(narrative_plan, dict):
        return None

    ordered = narrative_plan.get("ordered_concepts")
    if not isinstance(ordered, list):
        ordered = []

    segments: list[dict[str, Any]] = []
    for seg in narrative_plan.get("segments") or []:
        if not isinstance(seg, dict):
            continue
        segments.append(
            {
                "id": str(seg.get("id", "")).strip(),
                "concept_ref": str(seg.get("concept_ref", "")).strip(),
                "scene_focus": str(seg.get("scene_focus", "")).strip(),
                "transition_hook": str(seg.get("transition_hook", "")).strip()
                if seg.get("transition_hook") is not None
                else "",
                "duration_hint_s": int(seg.get("duration_hint_s", 0)) if isinstance(seg.get("duration_hint_s"), int) else 0,
            }
        )

    return {
        "global_arc": str(narrative_plan.get("global_arc", "")).strip(),
        "ordered_concepts": [str(x).strip() for x in ordered if str(x).strip()],
        "segments": segments,
    }


def _render_error_lines(errors: list[str], *, limit: int = 60) -> str:
    if not errors:
        return "(no validation errors)"
    lines = [f"- {err}" for err in errors[:limit]]
    if len(errors) > limit:
        lines.append(f"- ... and {len(errors) - limit} more errors")
    return "\n".join(lines)


def _focus_object_ids(
    *,
    roles: dict[str, str] | None,
    used_ids: set[str],
) -> set[str]:
    if not roles:
        return set()
    focus_roles = {"diagram", "core_eq", "conclusion", "check", "title"}
    result: set[str] = set()
    for object_id_raw, role_raw in roles.items():
        object_id = str(object_id_raw).strip()
        role = str(role_raw).strip().lower()
        if object_id and role in focus_roles and object_id in used_ids:
            result.add(object_id)
    return result


def _validate_layout_data(*, data: Any, draft: dict, enums: dict) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["layout root must be an object"]

    scenes = data.get("scenes")
    if not isinstance(scenes, list):
        return ["root.scenes must be an array"]

    expected_scene_ids = _draft_scene_ids(draft)
    expected_scene_set = set(expected_scene_ids)
    seen_scene_ids: set[str] = set()

    allowed_layout_types = set(enums["layout_types"])
    allowed_action_ops = set(enums["action_ops"])
    allowed_anims = set(enums["anims"])
    known_object_ids = _global_object_ids(draft)
    motion_span_by_scene = _scene_motion_span_map(draft)
    draft_scene_roles = _scene_role_summary(draft)

    scene_used_ids_map: dict[str, set[str]] = {}
    scene_keep_ids_map: dict[str, set[str]] = {}
    scene_focus_ids_map: dict[str, set[str]] = {}

    for scene_index, scene in enumerate(scenes):
        scene_path = f"scenes[{scene_index}]"
        if not isinstance(scene, dict):
            errors.append(f"{scene_path} must be an object")
            continue

        scene_id = str(scene.get("id", "")).strip()
        scene_motion_span = 0.0
        if not scene_id:
            errors.append(f"{scene_path}.id is required")
        else:
            if scene_id in seen_scene_ids:
                errors.append(f"{scene_path}.id duplicated: {scene_id}")
            seen_scene_ids.add(scene_id)
            if scene_id not in expected_scene_set:
                errors.append(f"{scene_path}.id not found in scene_draft: {scene_id}")
            scene_motion_span = float(motion_span_by_scene.get(scene_id, 0.0))

        for required_key in ("layout", "actions", "keep"):
            if required_key not in scene:
                errors.append(f"{scene_path}.{required_key} is required")

        used_ids: set[str] = set()
        scene_timeline_duration = 0.0
        keep_ids: set[str] = set()
        play_anims: list[str] = []
        roles_compact: dict[str, str] | None = None

        layout = scene.get("layout")
        if not isinstance(layout, dict):
            errors.append(f"{scene_path}.layout must be an object")
        else:
            layout_type = str(layout.get("type", "")).strip()
            slots = layout.get("slots")
            params = layout.get("params")
            placements = layout.get("placements")

            if not layout_type:
                errors.append(f"{scene_path}.layout.type is required")
            elif layout_type not in allowed_layout_types:
                errors.append(f"{scene_path}.layout.type not allowed: {layout_type}")
            if layout_type != "free":
                errors.append(f"{scene_path}.layout.type must be free in LLM3 output")
            if slots is not None:
                if not isinstance(slots, dict):
                    errors.append(f"{scene_path}.layout.slots must be an object when provided")
                elif slots:
                    errors.append(f"{scene_path}.layout.slots must be empty under free layout")
            if params is not None:
                if not isinstance(params, dict):
                    errors.append(f"{scene_path}.layout.params must be an object when provided")
                elif params:
                    errors.append(f"{scene_path}.layout.params must be empty under free layout")

            if not isinstance(placements, dict):
                errors.append(f"{scene_path}.layout.placements must be an object")
            elif not placements:
                errors.append(f"{scene_path}.layout.placements must not be empty")
            else:
                for object_id_raw, place in placements.items():
                    object_id = str(object_id_raw).strip()
                    if not object_id:
                        errors.append(f"{scene_path}.layout.placements has empty object id key")
                        continue
                    if object_id not in known_object_ids:
                        errors.append(f"{scene_path}.layout.placements unknown object id: {object_id}")
                        continue
                    used_ids.add(object_id)

                    place_path = f"{scene_path}.layout.placements[{object_id}]"
                    if not isinstance(place, dict):
                        errors.append(f"{place_path} must be an object")
                        continue
                    unknown_keys = sorted([k for k in place.keys() if k not in {"cx", "cy", "w", "h", "anchor"}])
                    if unknown_keys:
                        errors.append(f"{place_path} has unsupported keys: {', '.join(unknown_keys)}")
                    numeric_values: dict[str, float] = {}
                    for key in ("cx", "cy", "w", "h"):
                        value = _safe_float(place.get(key))
                        if value is None:
                            errors.append(f"{place_path}.{key} must be a number")
                            continue
                        numeric_values[key] = value
                        if key in {"cx", "cy"} and (value < 0.0 or value > 1.0):
                            errors.append(f"{place_path}.{key} out of range [0,1]: {value}")
                        if key in {"w", "h"} and (value <= 0.0 or value > 1.0):
                            errors.append(f"{place_path}.{key} out of range (0,1]: {value}")
                    anchor = str(place.get("anchor", "C")).strip().upper() or "C"
                    if anchor not in _ALLOWED_PLACEMENT_ANCHORS:
                        errors.append(
                            f"{place_path}.anchor not allowed: {anchor} "
                            f"(allowed: {', '.join(sorted(_ALLOWED_PLACEMENT_ANCHORS))})"
                        )

        actions = scene.get("actions")
        if not isinstance(actions, list):
            errors.append(f"{scene_path}.actions must be an array")
        else:
            for action_index, action in enumerate(actions):
                action_path = f"{scene_path}.actions[{action_index}]"
                if not isinstance(action, dict):
                    errors.append(f"{action_path} must be an object")
                    continue

                op = str(action.get("op", "")).strip().lower()
                if op not in allowed_action_ops:
                    errors.append(f"{action_path}.op not allowed: {action.get('op')}")
                    continue

                if op == "wait":
                    duration = _safe_float(action.get("duration"))
                    if duration is None:
                        errors.append(f"{action_path}.duration must be a number >= 0")
                        continue
                    if duration < 0:
                        errors.append(f"{action_path}.duration must be >= 0")
                        continue
                    scene_timeline_duration += duration
                    continue

                anim = str(action.get("anim", "")).strip()
                if anim not in allowed_anims:
                    errors.append(f"{action_path}.anim not allowed: {action.get('anim')}")
                else:
                    play_anims.append(anim)

                play_duration: float | None = None
                if "duration" in action:
                    play_duration = _safe_float(action.get("duration"))
                    if play_duration is None:
                        errors.append(f"{action_path}.duration must be a number > 0")
                    elif play_duration <= 0:
                        errors.append(f"{action_path}.duration must be > 0")
                        play_duration = None
                elif scene_motion_span > 0:
                    errors.append(f"{action_path}.duration is required when scene has graph.motions")

                if play_duration is not None:
                    scene_timeline_duration += play_duration

                targets_raw = action.get("targets")
                if targets_raw is None and "target" in action:
                    targets_raw = action.get("target")
                if targets_raw is None:
                    targets_raw = []
                if not isinstance(targets_raw, list):
                    single = str(targets_raw).strip()
                    targets_raw = [single] if single else []

                targets: list[str] = []
                for value in targets_raw:
                    object_id = str(value).strip()
                    if not object_id:
                        continue
                    targets.append(object_id)
                    if object_id not in known_object_ids:
                        errors.append(f"{action_path}.targets references unknown object id: {object_id}")
                    used_ids.add(object_id)

                src_raw = action.get("src")
                dst_raw = action.get("dst")
                src = str(src_raw).strip() if isinstance(src_raw, str) and src_raw.strip() else None
                dst = str(dst_raw).strip() if isinstance(dst_raw, str) and dst_raw.strip() else None

                if src:
                    if src not in known_object_ids:
                        errors.append(f"{action_path}.src unknown object id: {src}")
                    used_ids.add(src)
                if dst:
                    if dst not in known_object_ids:
                        errors.append(f"{action_path}.dst unknown object id: {dst}")
                    used_ids.add(dst)

                if anim in {"fade_in", "fade_out", "write", "create", "indicate"} and len(targets) < 1:
                    errors.append(f"{action_path} {anim} requires non-empty targets")

                if anim == "transform":
                    src_eff = src or (targets[0] if len(targets) >= 1 else None)
                    dst_eff = dst or (targets[1] if len(targets) >= 2 else None)
                    if not src_eff or not dst_eff:
                        errors.append(
                            f"{action_path} transform requires src+dst (or at least 2 targets)"
                        )

        if scene_motion_span > 0:
            if scene_timeline_duration <= 0:
                errors.append(f"{scene_path} has graph.motions but no effective timeline-driving action duration")
            elif scene_timeline_duration + 1e-6 < scene_motion_span:
                errors.append(
                    f"{scene_path} action duration {scene_timeline_duration:.3f}s is shorter than required motion span {scene_motion_span:.3f}s"
                )

        keep = scene.get("keep")
        if not isinstance(keep, list):
            errors.append(f"{scene_path}.keep must be an array")
        else:
            for keep_index, object_id_raw in enumerate(keep):
                object_id = str(object_id_raw).strip()
                if not object_id:
                    errors.append(f"{scene_path}.keep[{keep_index}] must be non-empty object id")
                    continue
                if object_id not in known_object_ids:
                    errors.append(f"{scene_path}.keep[{keep_index}] unknown object id: {object_id}")
                used_ids.add(object_id)
                keep_ids.add(object_id)

        roles = scene.get("roles")
        if roles is not None:
            if not isinstance(roles, dict):
                errors.append(f"{scene_path}.roles must be an object when provided")
            else:
                roles_compact = {}
                for object_id_raw in roles.keys():
                    object_id = str(object_id_raw).strip()
                    if not object_id:
                        continue
                    if object_id not in known_object_ids:
                        errors.append(f"{scene_path}.roles references unknown object id: {object_id}")
                        continue
                    if object_id not in used_ids:
                        errors.append(
                            f"{scene_path}.roles references object not used in this scene: {object_id}"
                        )
                    role_raw = roles.get(object_id_raw)
                    role = str(role_raw).strip()
                    if role:
                        roles_compact[object_id] = role

        # Quality checks (focus / rhythm) are soft constraints but enforced here
        # so repair loop can fix low-quality structure before rendering.
        explicit_roles_provided = roles_compact is not None
        role_source = roles_compact if explicit_roles_provided else (draft_scene_roles.get(scene_id) or {})
        focus_ids = _focus_object_ids(roles=role_source, used_ids=used_ids)
        if role_source:
            if not focus_ids:
                errors.append(
                    f"{scene_path} quality: no focus object used "
                    "(expected role in diagram/core_eq/conclusion/check/title)"
                )
            elif explicit_roles_provided and len(focus_ids) > 2:
                errors.append(
                    f"{scene_path} quality: too many focus objects ({len(focus_ids)}), keep 1-2 focus objects"
                )

        emphasis_anims = {"write", "create", "indicate", "transform"}
        if len(play_anims) >= 3 and not any(anim in emphasis_anims for anim in play_anims):
            errors.append(
                f"{scene_path} quality: action rhythm lacks emphasis "
                "(need at least one of write/create/indicate/transform)"
            )

        if scene_id:
            scene_used_ids_map[scene_id] = set(used_ids)
            scene_keep_ids_map[scene_id] = set(keep_ids)
            scene_focus_ids_map[scene_id] = set(focus_ids)

    missing_scene_ids = sorted(expected_scene_set - seen_scene_ids)
    for missing in missing_scene_ids:
        errors.append(f"scene missing in layout output: {missing}")

    # Cross-scene continuity: if next scene's focus object already appears in current scene,
    # prefer continuity via keep.
    for current_scene_id, next_scene_id in zip(expected_scene_ids, expected_scene_ids[1:]):
        current_used = scene_used_ids_map.get(current_scene_id, set())
        current_keep = scene_keep_ids_map.get(current_scene_id, set())
        next_focus = scene_focus_ids_map.get(next_scene_id, set())
        if not current_used or not next_focus:
            continue
        should_continue = sorted((current_used & next_focus) - current_keep)
        if should_continue:
            preview = ", ".join(should_continue[:3])
            errors.append(
                f"scene transition quality {current_scene_id}->{next_scene_id}: "
                f"focus continuity object(s) should be kept: {preview}"
            )

    return errors


def _parse_and_validate(*, content: str, draft: dict, enums: dict) -> tuple[dict[str, Any] | None, list[str]]:
    try:
        data = load_json_from_llm(content)
    except Exception as exc:  # noqa: BLE001
        return None, [f"JSON parse failed: {exc}"]

    errors = _validate_layout_data(data=data, draft=draft, enums=enums)
    return (data if not errors else None), errors


def _build_user_payload(*, draft: dict, enums: dict, narrative_plan: dict[str, Any] | None) -> str:
    pedagogy = draft.get("pedagogy_plan")
    scene_roles = _scene_role_summary(draft)
    scene_objects = _scene_object_catalog(draft)
    scene_ids = _draft_scene_ids(draft)
    compact_narrative_plan = _compact_narrative_plan(narrative_plan)
    allowed_layout_types = [layout_type for layout_type in sorted(enums["layout_types"]) if layout_type == "free"] or [
        "free"
    ]
    return "\n".join(
        [
            "你要输出 scene_layout.json。只做布局和动作，不修改 scene_draft 的对象语义。",
            "",
            "强制布局类型（仅允许）：",
            json.dumps(allowed_layout_types, ensure_ascii=False),
            "",
            "允许的 action.op：",
            json.dumps(sorted(enums["action_ops"]), ensure_ascii=False),
            "",
            "允许的 anim：",
            json.dumps(sorted(enums["anims"]), ensure_ascii=False),
            "",
            "自由布局 placements 规范：",
            json.dumps(
                {
                    "object_id": {
                        "cx": "float in [0,1]",
                        "cy": "float in [0,1]",
                        "w": "float in (0,1]",
                        "h": "float in (0,1]",
                        "anchor": "one of C/U/D/L/R/UL/UR/DL/DR (default C)",
                    }
                },
                ensure_ascii=False,
                indent=2,
            ),
            "",
            "布局策略提示：",
            json.dumps(_layout_strategy_hints(), ensure_ascii=False, indent=2),
            "",
            "必须覆盖的 scene id（一一对应，不能缺失）：",
            json.dumps(scene_ids, ensure_ascii=False),
            "",
            "每个 scene 可用对象 id：",
            json.dumps(scene_objects, ensure_ascii=False, indent=2),
            "",
            "pedagogy_plan（可选）：",
            json.dumps(pedagogy, ensure_ascii=False, indent=2),
            "",
            "scene 角色摘要（若存在，优先按角色决定主次和版面重心）：",
            json.dumps(scene_roles, ensure_ascii=False, indent=2),
            "",
            "narrative_plan（可选，若存在请对齐其节奏与转场）：",
            json.dumps(compact_narrative_plan, ensure_ascii=False, indent=2) if compact_narrative_plan is not None else "{}",
            "",
            "scene_draft.json：",
            json.dumps(draft, ensure_ascii=False, indent=2),
            "",
            "若 scene_draft 某幕包含 narrative_storyboard，请优先按其 animation_steps 组织 actions 时序。",
            "",
            "硬性输出合同：",
            "1) 只输出一个 JSON 对象，不要 Markdown，不要解释。",
            "2) 根对象必须包含 scenes 数组，且 scene id 与 scene_draft 一一对应。",
            "3) 每个 scene 必须包含 id/layout/actions/keep。",
            "4) 每个 scene.layout 必须包含 type 与 placements，且 type 必须为 free。",
            "5) free 布局下 layout.slots 与 layout.params 必须为空对象，或直接省略。",
            "6) 禁止发明新 object id；所有 id 必须来自 scene_draft。",
            "7) 若输出 roles，roles 里的对象必须在本 scene 的 placements/actions/keep 中实际使用。",
            "8) 若提供 narrative_plan，尽量保持 segment 对应 scene 的主焦点与 transition_hook。",
            "",
            "动作合同（必须遵守）：",
            "A) wait: 必须有 duration >= 0。",
            "B) fade_in/fade_out/write/create/indicate: targets 必须非空。",
            "C) transform: 必须满足其一：",
            "   - 提供 src 与 dst；",
            "   - 或 targets 至少 2 个（第 1 个作 src，第 2 个作 dst）。",
            "D) 严禁 transform 只有 1 个 target。",
            "E) 如果不确定 transform 参数，改用 write/fade_in/fade_out。",
        ]
    )

def _build_repair_payload(
    *,
    draft: dict,
    enums: dict,
    narrative_plan: dict[str, Any] | None,
    raw_content: str,
    errors: list[str],
    round_index: int,
) -> str:
    pedagogy = draft.get("pedagogy_plan")
    scene_roles = _scene_role_summary(draft)
    scene_objects = _scene_object_catalog(draft)
    scene_ids = _draft_scene_ids(draft)
    compact_narrative_plan = _compact_narrative_plan(narrative_plan)
    allowed_layout_types = [layout_type for layout_type in sorted(enums["layout_types"]) if layout_type == "free"] or [
        "free"
    ]
    return "\n".join(
        [
            f"这是第 {round_index} 轮修复。请在最小改动下修复 scene_layout.json。",
            "只输出严格 JSON，不要解释。",
            "",
            "必须修复的错误：",
            _render_error_lines(errors),
            "",
            "强制布局类型（仅允许）：",
            json.dumps(allowed_layout_types, ensure_ascii=False),
            "",
            "允许的 action.op：",
            json.dumps(sorted(enums["action_ops"]), ensure_ascii=False),
            "",
            "允许的 anim：",
            json.dumps(sorted(enums["anims"]), ensure_ascii=False),
            "",
            "自由布局 placements 规范：",
            json.dumps(
                {
                    "object_id": {
                        "cx": "float in [0,1]",
                        "cy": "float in [0,1]",
                        "w": "float in (0,1]",
                        "h": "float in (0,1]",
                        "anchor": "one of C/U/D/L/R/UL/UR/DL/DR",
                    }
                },
                ensure_ascii=False,
                indent=2,
            ),
            "",
            "布局策略提示：",
            json.dumps(_layout_strategy_hints(), ensure_ascii=False, indent=2),
            "",
            "必须覆盖的 scene id：",
            json.dumps(scene_ids, ensure_ascii=False),
            "",
            "每个 scene 可用对象 id：",
            json.dumps(scene_objects, ensure_ascii=False, indent=2),
            "",
            "pedagogy_plan（可选）：",
            json.dumps(pedagogy, ensure_ascii=False, indent=2),
            "",
            "scene 角色摘要：",
            json.dumps(scene_roles, ensure_ascii=False, indent=2),
            "",
            "narrative_plan（可选，若存在请保持节奏与转场语义）：",
            json.dumps(compact_narrative_plan, ensure_ascii=False, indent=2) if compact_narrative_plan is not None else "{}",
            "",
            "scene_draft.json：",
            json.dumps(draft, ensure_ascii=False, indent=2),
            "",
            "若 scene_draft 某幕包含 narrative_storyboard，请优先按其 animation_steps 组织 actions 时序。",
            "",
            "参考结构示例：",
            json.dumps(
                {
                    "scenes": [
                        {
                            "id": "S1",
                            "layout": {
                                "type": "free",
                                "placements": {
                                    "o_diagram": {"cx": 0.33, "cy": 0.55, "w": 0.58, "h": 0.82, "anchor": "C"},
                                    "o_text": {"cx": 0.77, "cy": 0.62, "w": 0.40, "h": 0.40, "anchor": "C"},
                                },
                            },
                            "actions": [
                                {"op": "play", "anim": "fade_in", "targets": ["o_diagram"]},
                                {"op": "wait", "duration": 0.4},
                                {"op": "play", "anim": "write", "targets": ["o_text"]},
                            ],
                            "keep": ["o_diagram", "o_text"],
                            "roles": {"o_diagram": "diagram", "o_text": "support_eq"},
                        }
                    ]
                },
                ensure_ascii=False,
                indent=2,
            ),
            "",
            "待修复 JSON：",
            raw_content.strip(),
            "",
            "再次重申动作合同：",
            "- transform 必须有 src+dst，或 targets 至少 2 个。",
            "- 不能出现 transform 只有 1 个 target。",
            "- 若无法保证 transform 合法，请改为 write/fade_in/fade_out。",
            "- 若提供 narrative_plan，修复后仍要保持对应 scene 的主焦点与转场钩子语义。",
            "- layout.type 只能是 free，layout.placements 不能为空。",
            "",
            "仅输出修复后的 JSON。",
        ]
    )

def main() -> int:
    parser = argparse.ArgumentParser(description="LLM3: generate scene_layout.json")
    parser.add_argument("--case", default="cases/demo_001", help="Case directory, e.g. cases/demo_001")
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
    generate_llm_cfg = load_zhipu_stage_config("llm3", "generate", base_cfg=base_llm_cfg)
    continue_llm_cfg = load_zhipu_stage_config("llm3", "continue", base_cfg=base_llm_cfg)
    repair_llm_cfg = load_zhipu_stage_config("llm3", "repair", base_cfg=base_llm_cfg)

    case_dir = Path(args.case)
    draft = json.loads((case_dir / "scene_draft.json").read_text(encoding="utf-8"))
    narrative_plan_path = Path(args.narrative_plan) if args.narrative_plan else (case_dir / "narrative_plan.json")
    narrative_plan: dict[str, Any] | None = None
    if narrative_plan_path.exists():
        try:
            parsed = json.loads(narrative_plan_path.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            print(f"Invalid narrative_plan.json: {exc}", file=sys.stderr)
            return 2
        if isinstance(parsed, dict):
            narrative_plan = parsed
    elif args.narrative_plan:
        print(f"Missing specified narrative plan file: {narrative_plan_path}", file=sys.stderr)
        return 2

    out_path = case_dir / "scene_layout.json"
    errors_path = case_dir / "llm3_validation_errors.txt"
    system_prompt_path = case_dir / "llm3_system_prompt.txt"

    enums = load_enums()
    prompt = compose_prompt(
        "llm3",
        context={"has_narrative_plan": narrative_plan is not None},
    )
    system_prompt_path.write_text(prompt.strip() + "\n", encoding="utf-8")
    user_payload = _build_user_payload(draft=draft, enums=enums, narrative_plan=narrative_plan)

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

    raw_path = case_dir / "llm3_raw.txt"
    raw_path.write_text(content.strip() + "\n", encoding="utf-8")
    _write_continuation_chunks(case_dir, "llm3_continue_raw", cont_chunks)

    validation_log: list[str] = []
    data, errors = _parse_and_validate(content=content, draft=draft, enums=enums)
    if errors:
        validation_log.append("[initial]")
        validation_log.extend(errors)
        validation_log.append("")

    if errors and args.no_repair:
        errors_path.write_text("\n".join(validation_log).strip() + "\n", encoding="utf-8")
        print(f"LLM3 output parse/validation failed. See: {raw_path} and {errors_path}", file=sys.stderr)
        return 2

    if errors:
        repair_prompt = load_prompt("json_repair.md")
        current_content = content
        repair_raw_path = case_dir / "llm3_repair_raw.txt"

        for round_index in range(1, max(1, args.repair_rounds) + 1):
            repair_payload = _build_repair_payload(
                draft=draft,
                enums=enums,
                narrative_plan=narrative_plan,
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
            (case_dir / f"llm3_repair_raw_round_{round_index}.txt").write_text(
                repaired.strip() + "\n", encoding="utf-8"
            )
            _write_continuation_chunks(case_dir, f"llm3_repair_continue_raw_r{round_index}", repair_cont_chunks)

            data, errors = _parse_and_validate(content=repaired, draft=draft, enums=enums)
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
                "LLM3 repair rounds finished but output is still invalid. "
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


