from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from layout.templates import TEMPLATE_REGISTRY
from pipeline.config import load_enums
from pipeline.env import load_dotenv
from pipeline.json_utils import load_json_from_llm
from pipeline.llm.types import ChatMessage
from pipeline.llm.zhipu import chat_completion
from pipeline.llm_continuation import continue_json_output
from pipeline.prompting import load_prompt


def _write_continuation_chunks(case_dir: Path, stem: str, chunks: list[str]) -> None:
    for idx, chunk in enumerate(chunks, start=1):
        (case_dir / f"{stem}_{idx}.txt").write_text(chunk.strip() + "\n", encoding="utf-8")


def _template_slot_catalog() -> dict[str, list[str]]:
    return {template_type: list(template.slot_order) for template_type, template in TEMPLATE_REGISTRY.items()}


def _template_param_catalog() -> dict[str, dict]:
    slot_scales_doc = {
        "slot_scales": {
            "type": "object",
            "desc": "Per-slot width/height scale",
            "value_schema": {"w": "float(0.2~1.0)", "h": "float(0.2~1.0)"},
            "example": {"left1": {"w": 0.9, "h": 0.7}},
        }
    }
    return {template_type: slot_scales_doc for template_type in TEMPLATE_REGISTRY}


def _layout_strategy_hints() -> dict[str, Any]:
    return {
        "count_based": {
            "1-2": "hero_side or left_right",
            "3-4": "grid_2x2",
            "5-6": "left3_right3",
            "7-8": "left4_right4",
            "9": "grid_3x3",
        },
        "role_based": {
            "contains_diagram_plus_text": "Prefer left_right (left=diagram, right=text/equation/conclusion)",
            "single_main_object": "Prefer hero_side (hero=main object, side=support text)",
            "multiple_equations": "Prefer left3_right3 and stack equations in right slots by reading order",
        },
        "readability": [
            "Keep one visual focus per scene.",
            "Avoid packing too many formulas in one scene.",
            "Reserve a dedicated slot for conclusion/check text when possible.",
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


def _render_error_lines(errors: list[str], *, limit: int = 60) -> str:
    if not errors:
        return "(no validation errors)"
    lines = [f"- {err}" for err in errors[:limit]]
    if len(errors) > limit:
        lines.append(f"- ... and {len(errors) - limit} more errors")
    return "\n".join(lines)


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

    slot_catalog = _template_slot_catalog()
    allowed_layout_types = set(enums["layout_types"])
    allowed_action_ops = set(enums["action_ops"])
    allowed_anims = set(enums["anims"])
    known_object_ids = _global_object_ids(draft)
    motion_span_by_scene = _scene_motion_span_map(draft)

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

        layout = scene.get("layout")
        if not isinstance(layout, dict):
            errors.append(f"{scene_path}.layout must be an object")
        else:
            layout_type = str(layout.get("type", "")).strip()
            slots = layout.get("slots")
            params = layout.get("params", {})

            if not layout_type:
                errors.append(f"{scene_path}.layout.type is required")
            elif layout_type not in allowed_layout_types:
                errors.append(f"{scene_path}.layout.type not allowed: {layout_type}")

            valid_slots = set(slot_catalog.get(layout_type, []))
            if not isinstance(slots, dict):
                errors.append(f"{scene_path}.layout.slots must be an object")
            else:
                for slot_id, object_id_raw in slots.items():
                    slot_key = str(slot_id).strip()
                    object_id = str(object_id_raw).strip()
                    if valid_slots and slot_key not in valid_slots:
                        errors.append(f"{scene_path}.layout.slots has invalid slot key: {slot_key}")
                    if not object_id:
                        errors.append(f"{scene_path}.layout.slots[{slot_key}] must be non-empty object id")
                        continue
                    if object_id not in known_object_ids:
                        errors.append(f"{scene_path}.layout.slots[{slot_key}] unknown object id: {object_id}")
                    used_ids.add(object_id)

            if not isinstance(params, dict):
                errors.append(f"{scene_path}.layout.params must be an object")
            else:
                unknown_param_keys = sorted([k for k in params.keys() if k != "slot_scales"])
                if unknown_param_keys:
                    errors.append(
                        f"{scene_path}.layout.params has unsupported keys: {', '.join(unknown_param_keys)}"
                    )
                slot_scales = params.get("slot_scales")
                if slot_scales is not None:
                    if not isinstance(slot_scales, dict):
                        errors.append(f"{scene_path}.layout.params.slot_scales must be an object")
                    else:
                        for slot_id, scale in slot_scales.items():
                            slot_key = str(slot_id).strip()
                            if valid_slots and slot_key not in valid_slots:
                                errors.append(
                                    f"{scene_path}.layout.params.slot_scales has invalid slot key: {slot_key}"
                                )
                            if not isinstance(scale, dict):
                                errors.append(
                                    f"{scene_path}.layout.params.slot_scales[{slot_key}] must be an object"
                                )
                                continue
                            unknown_scale_keys = sorted([k for k in scale.keys() if k not in {"w", "h"}])
                            if unknown_scale_keys:
                                errors.append(
                                    f"{scene_path}.layout.params.slot_scales[{slot_key}] has unsupported keys: "
                                    + ", ".join(unknown_scale_keys)
                                )
                            for dim in ("w", "h"):
                                if dim not in scale:
                                    continue
                                try:
                                    value = float(scale[dim])
                                except (TypeError, ValueError):
                                    errors.append(
                                        f"{scene_path}.layout.params.slot_scales[{slot_key}].{dim} must be float in [0.2,1.0]"
                                    )
                                    continue
                                if value < 0.2 or value > 1.0:
                                    errors.append(
                                        f"{scene_path}.layout.params.slot_scales[{slot_key}].{dim} out of range [0.2,1.0]: {value}"
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

        roles = scene.get("roles")
        if roles is not None:
            if not isinstance(roles, dict):
                errors.append(f"{scene_path}.roles must be an object when provided")
            else:
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

    missing_scene_ids = sorted(expected_scene_set - seen_scene_ids)
    for missing in missing_scene_ids:
        errors.append(f"scene missing in layout output: {missing}")

    return errors


def _parse_and_validate(*, content: str, draft: dict, enums: dict) -> tuple[dict[str, Any] | None, list[str]]:
    try:
        data = load_json_from_llm(content)
    except Exception as exc:  # noqa: BLE001
        return None, [f"JSON parse failed: {exc}"]

    errors = _validate_layout_data(data=data, draft=draft, enums=enums)
    return (data if not errors else None), errors


def _build_user_payload(*, draft: dict, enums: dict) -> str:
    pedagogy = draft.get("pedagogy_plan")
    scene_roles = _scene_role_summary(draft)
    scene_objects = _scene_object_catalog(draft)
    scene_ids = _draft_scene_ids(draft)
    return "\n".join(
        [
            "你要输出 scene_layout.json。只做布局和动作，不改 scene_draft 的对象语义。",
            "",
            "允许的 layout.type：",
            json.dumps(sorted(enums["layout_types"]), ensure_ascii=False),
            "",
            "允许的 action.op：",
            json.dumps(sorted(enums["action_ops"]), ensure_ascii=False),
            "",
            "允许的 anim：",
            json.dumps(sorted(enums["anims"]), ensure_ascii=False),
            "",
            "模板槽位目录（slots 的 key 只能从这里选）：",
            json.dumps(_template_slot_catalog(), ensure_ascii=False, indent=2),
            "",
            "模板参数规范（仅允许 params.slot_scales）：",
            json.dumps(_template_param_catalog(), ensure_ascii=False, indent=2),
            "",
            "布局策略提示：",
            json.dumps(_layout_strategy_hints(), ensure_ascii=False, indent=2),
            "",
            "必须覆盖的 scene id（一一对应，不可缺失）：",
            json.dumps(scene_ids, ensure_ascii=False),
            "",
            "每个 scene 可用对象 id：",
            json.dumps(scene_objects, ensure_ascii=False, indent=2),
            "",
            "pedagogy_plan（可选）：",
            json.dumps(pedagogy, ensure_ascii=False, indent=2),
            "",
            "scene 角色摘要（若存在，优先按角色分配槽位）：",
            json.dumps(scene_roles, ensure_ascii=False, indent=2),
            "",
            "scene_draft.json：",
            json.dumps(draft, ensure_ascii=False, indent=2),
            "",
            "硬性输出合同：",
            "1) 只输出一个 JSON 对象，不要 Markdown，不要解释。",
            "2) 根对象必须包含 scenes 数组，且 scene id 与 scene_draft 一一对应。",
            "3) 每个 scene 必须包含 id/layout/actions/keep。",
            "4) scene.layout 必须包含 type/slots；slots 键名必须合法。",
            "5) 不允许绝对坐标；只允许 slot 布局。",
            "6) layout.params 只允许 slot_scales。",
            "7) 所有对象 id 必须来自 scene_draft，不允许发明新 id。",
            "8) 如果输出 roles，roles 中对象必须在本 scene 的 slots/actions/keep 中实际使用。",
            "",
            "动作合同（必须遵守）：",
            "A) wait: 必须有 duration >= 0。",
            "B) fade_in/fade_out/write/create/indicate: targets 必须非空。",
            "C) transform: 必须满足其一：",
            "   - 提供 src 和 dst；",
            "   - 或 targets 至少 2 个（第1个作 src，第2个作 dst）。",
            "D) 严禁 transform 只有一个 target。",
            "E) 如果不确定 transform 参数，改用 write/fade_in/fade_out。",
        ]
    )


def _build_repair_payload(
    *,
    draft: dict,
    enums: dict,
    raw_content: str,
    errors: list[str],
    round_index: int,
) -> str:
    pedagogy = draft.get("pedagogy_plan")
    scene_roles = _scene_role_summary(draft)
    scene_objects = _scene_object_catalog(draft)
    scene_ids = _draft_scene_ids(draft)
    return "\n".join(
        [
            f"这是第 {round_index} 轮修复。请在最小改动下修复 scene_layout.json。",
            "只输出严格 JSON，不要解释。",
            "",
            "必须修复的错误：",
            _render_error_lines(errors),
            "",
            "允许的 layout.type：",
            json.dumps(sorted(enums["layout_types"]), ensure_ascii=False),
            "",
            "允许的 action.op：",
            json.dumps(sorted(enums["action_ops"]), ensure_ascii=False),
            "",
            "允许的 anim：",
            json.dumps(sorted(enums["anims"]), ensure_ascii=False),
            "",
            "模板槽位目录：",
            json.dumps(_template_slot_catalog(), ensure_ascii=False, indent=2),
            "",
            "模板参数规范（仅 slot_scales）：",
            json.dumps(_template_param_catalog(), ensure_ascii=False, indent=2),
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
            "scene_draft.json：",
            json.dumps(draft, ensure_ascii=False, indent=2),
            "",
            "参考结构示例：",
            json.dumps(
                {
                    "scenes": [
                        {
                            "id": "S1",
                            "layout": {
                                "type": "left_right",
                                "slots": {"left": "o_diagram", "right": "o_text"},
                                "params": {"slot_scales": {"left": {"w": 0.95, "h": 0.9}}},
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
            "- 如果无法保证 transform 合法，请改为 write/fade_in/fade_out。",
            "",
            "仅输出修复后的 JSON。",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="LLM3: generate scene_layout.json")
    parser.add_argument("--case", default="cases/demo_001", help="Case directory, e.g. cases/demo_001")
    parser.add_argument("--no-repair", action="store_true", help="Skip repair when parse/validation fails")
    parser.add_argument("--continue-rounds", type=int, default=2, help="Max continuation rounds for truncated JSON")
    parser.add_argument("--repair-rounds", type=int, default=2, help="Max validation-driven repair rounds")
    args = parser.parse_args()

    load_dotenv()

    case_dir = Path(args.case)
    draft = json.loads((case_dir / "scene_draft.json").read_text(encoding="utf-8"))
    out_path = case_dir / "scene_layout.json"
    errors_path = case_dir / "llm3_validation_errors.txt"

    enums = load_enums()
    prompt = load_prompt("llm3_scene_layout.md")
    user_payload = _build_user_payload(draft=draft, enums=enums)

    content = chat_completion([ChatMessage(role="system", content=prompt), ChatMessage(role="user", content=user_payload)])
    content, cont_chunks = continue_json_output(
        content,
        system_prompt=prompt,
        user_payload=user_payload,
        parse_fn=load_json_from_llm,
        max_rounds=args.continue_rounds,
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
                raw_content=current_content,
                errors=errors,
                round_index=round_index,
            )
            repaired = chat_completion(
                [ChatMessage(role="system", content=repair_prompt), ChatMessage(role="user", content=repair_payload)]
            )
            repaired, repair_cont_chunks = continue_json_output(
                repaired,
                system_prompt=repair_prompt,
                user_payload=repair_payload,
                parse_fn=load_json_from_llm,
                max_rounds=args.continue_rounds,
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
