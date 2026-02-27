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
from schema.scene_semantic_models import SceneSemanticPlan


_CUSTOM_ROLE_ALLOWED = {"new_component", "special_motion", "complex_effect"}
_CODEGEN_SCOPE_ALLOWED = {"object", "motion", "effect", "hybrid"}
_CODEGEN_KIND_ALLOWED = _CUSTOM_ROLE_ALLOWED | {"hybrid", "custom"}
_TOP_LEVEL_OBJECT_TYPES: tuple[str, ...] = (
    "TextBlock",
    "BulletPanel",
    "Formula",
    "CompositeObject",
    "CustomObject",
)
_COMPONENTS_CATALOG_PATH = Path(__file__).resolve().parents[1] / "llm_constraints" / "specs" / "components_catalog.json"

def _write_continuation_chunks(case_dir: Path, stem: str, chunks: list[str]) -> None:
    for idx, chunk in enumerate(chunks, start=1):
        (case_dir / f"{stem}_{idx}.txt").write_text(chunk.strip() + "\n", encoding="utf-8")


def _render_error_lines(errors: list[str], *, limit: int = 50) -> str:
    if not errors:
        return "(no validation errors)"
    lines = [f"- {err}" for err in errors[:limit]]
    if len(errors) > limit:
        lines.append(f"- ... and {len(errors) - limit} more errors")
    return "\n".join(lines)


def _load_part_reference_hints() -> dict[str, dict[str, str]]:
    """
    Load part reference hints from llm_constraints/specs/components_catalog.json.
    This is the only source used by llm2 for component reference visibility.
    """
    try:
        payload = json.loads(_COMPONENTS_CATALOG_PATH.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}

    components = payload.get("components")
    if not isinstance(components, dict):
        return {}

    hints: dict[str, dict[str, str]] = {}
    for key, value in components.items():
        part_type = str(key).strip()
        if not part_type or not isinstance(value, dict):
            continue

        what = str(value.get("label", "")).strip()
        when_to_use = str(value.get("purpose", "")).strip()
        if not what:
            what = f"{part_type} component"
        if not when_to_use:
            when_to_use = f"Use {part_type} inside CompositeObject drawing semantics."

        hints[part_type] = {"what": what, "when_to_use": when_to_use}

    return hints


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


def _compact_narrative_plan(narrative_plan: Any) -> dict[str, Any] | None:
    if not isinstance(narrative_plan, dict):
        return None

    analysis = narrative_plan.get("analysis")
    analysis_compact = analysis if isinstance(analysis, dict) else {}
    ordered = narrative_plan.get("ordered_concepts")
    if not isinstance(ordered, list):
        ordered = []

    segments_compact: list[dict[str, Any]] = []
    for seg in narrative_plan.get("segments") or []:
        if not isinstance(seg, dict):
            continue
        equations = seg.get("key_equations")
        segments_compact.append(
            {
                "id": str(seg.get("id", "")).strip(),
                "concept_ref": str(seg.get("concept_ref", "")).strip(),
                "sub_question_id": str(seg.get("sub_question_id", "")).strip() if seg.get("sub_question_id") is not None else "",
                "title": str(seg.get("title", "")).strip(),
                "scene_focus": str(seg.get("scene_focus", "")).strip(),
                "visual_intent": str(seg.get("visual_intent", "")).strip(),
                "transition_hook": str(seg.get("transition_hook", "")).strip()
                if seg.get("transition_hook") is not None
                else "",
                "duration_hint_s": int(seg.get("duration_hint_s", 0)) if isinstance(seg.get("duration_hint_s"), int) else 0,
                "key_equations": equations if isinstance(equations, list) else [],
            }
        )

    return {
        "analysis": {
            "target_concept": str(analysis_compact.get("target_concept", "")).strip(),
            "narrative_goal": str(analysis_compact.get("narrative_goal", "")).strip(),
            "audience_level": str(analysis_compact.get("audience_level", "")).strip(),
        },
        "global_arc": str(narrative_plan.get("global_arc", "")).strip(),
        "ordered_concepts": [str(x).strip() for x in ordered if str(x).strip()],
        "segments": segments_compact,
    }


def _is_nonempty_str(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _validate_custom_object_hints(model: SceneSemanticPlan) -> list[str]:
    errors: list[str] = []
    for scene_index, scene in enumerate(model.scenes):
        for object_index, obj in enumerate(scene.objects):
            if obj.type != "CustomObject":
                continue

            path = f"scenes[{scene_index}].objects[{object_index}] ({obj.id})"
            params = dict(obj.params or {})

            role = params.get("custom_role")
            if not _is_nonempty_str(role):
                errors.append(f"{path} CustomObject needs params.custom_role")
            else:
                role_text = str(role).strip()
                if role_text not in _CUSTOM_ROLE_ALLOWED:
                    allowed = ", ".join(sorted(_CUSTOM_ROLE_ALLOWED))
                    errors.append(f"{path} params.custom_role='{role_text}' invalid; allowed: {allowed}")

            draw_prompt = params.get("draw_prompt")
            if not _is_nonempty_str(draw_prompt):
                errors.append(f"{path} CustomObject needs params.draw_prompt (non-empty string)")

            motion_prompt = params.get("motion_prompt")
            if not _is_nonempty_str(motion_prompt):
                errors.append(f"{path} CustomObject needs params.motion_prompt (non-empty string)")

            api_hints = params.get("manim_api_hints")
            if api_hints is not None:
                if not isinstance(api_hints, list):
                    errors.append(f"{path} params.manim_api_hints must be an array when provided")
                elif not all(_is_nonempty_str(item) for item in api_hints):
                    errors.append(f"{path} params.manim_api_hints must contain non-empty strings only")

            motion_span_hint = params.get("motion_span_s_hint")
            if motion_span_hint is not None:
                try:
                    motion_span = float(motion_span_hint)
                except (TypeError, ValueError):
                    errors.append(f"{path} params.motion_span_s_hint must be a number when provided")
                else:
                    if motion_span <= 0:
                        errors.append(f"{path} params.motion_span_s_hint must be > 0 when provided")

            codegen_request = params.get("codegen_request")
            if not isinstance(codegen_request, dict):
                errors.append(f"{path} CustomObject needs params.codegen_request (object)")
                continue

            enabled = codegen_request.get("enabled")
            if not isinstance(enabled, bool):
                errors.append(f"{path} params.codegen_request.enabled must be true/false")

            scope = codegen_request.get("scope")
            if not _is_nonempty_str(scope):
                errors.append(f"{path} params.codegen_request.scope must be a non-empty string")
            else:
                scope_text = str(scope).strip().lower()
                if scope_text not in _CODEGEN_SCOPE_ALLOWED:
                    allowed = ", ".join(sorted(_CODEGEN_SCOPE_ALLOWED))
                    errors.append(f"{path} params.codegen_request.scope='{scope_text}' invalid; allowed: {allowed}")

            intent = codegen_request.get("intent")
            if not _is_nonempty_str(intent):
                errors.append(f"{path} params.codegen_request.intent must be a non-empty string")

            kind_hint = codegen_request.get("kind_hint")
            if kind_hint is not None:
                if not _is_nonempty_str(kind_hint):
                    errors.append(f"{path} params.codegen_request.kind_hint must be a non-empty string when provided")
                else:
                    kind_text = str(kind_hint).strip().lower()
                    if kind_text not in _CODEGEN_KIND_ALLOWED:
                        allowed = ", ".join(sorted(_CODEGEN_KIND_ALLOWED))
                        errors.append(f"{path} params.codegen_request.kind_hint='{kind_text}' invalid; allowed: {allowed}")
    return errors


def _build_part_reference_catalog(
    allowed_object_types: set[str],
    *,
    part_reference_hints: dict[str, dict[str, str]],
) -> list[dict[str, str]]:
    allowed_part_types = {t for t in allowed_object_types if t not in set(_TOP_LEVEL_OBJECT_TYPES)}
    catalog_part_types = set(part_reference_hints.keys())
    part_types = sorted(allowed_part_types | catalog_part_types)

    catalog: list[dict[str, str]] = []
    for part_type in part_types:
        hint = part_reference_hints.get(part_type, {})
        what = str(hint.get("what", "")).strip() or f"{part_type} component"
        when_to_use = str(hint.get("when_to_use", "")).strip() or (
            f"Use {part_type} inside CompositeObject drawing semantics."
        )
        catalog.append(
            {
                "type": part_type,
                "what": what,
                "when_to_use": when_to_use,
            }
        )
    return catalog


def _validate_part_reference_catalog(
    *,
    allowed_object_types: set[str],
    catalog: list[dict[str, str]],
) -> list[str]:
    errors: list[str] = []
    expected = {t for t in allowed_object_types if t not in set(_TOP_LEVEL_OBJECT_TYPES)}
    actual = {
        str(item.get("type", "")).strip()
        for item in catalog
        if isinstance(item, dict) and str(item.get("type", "")).strip()
    }

    missing = sorted(expected - actual)
    if missing:
        errors.append(f"part_reference_catalog missing enabled types: {missing}")

    if "Arrow" in expected and "Arrow" not in actual:
        errors.append("part_reference_catalog must include Arrow")
    return errors


def _build_user_payload(
    *,
    problem: str,
    teaching_plan: dict[str, Any] | None,
    narrative_plan: dict[str, Any] | None,
    allowed_object_types: set[str],
    part_reference_catalog: list[dict[str, str]],
) -> str:
    top_level_allowed = [x for x in _TOP_LEVEL_OBJECT_TYPES if x in allowed_object_types]
    compact_teaching = _compact_teaching_plan(teaching_plan)
    compact_narrative = _compact_narrative_plan(narrative_plan)
    lines = [
        "题目：",
        problem.strip(),
        "",
        "允许的顶层 object.type：",
        json.dumps(top_level_allowed, ensure_ascii=False, indent=2),
        "",
        "CompositeObject part.type 参考清单（仅供语义提示，禁止作为 objects[].type）：",
        "（来源：llm_constraints/specs/components_catalog.json）",
        json.dumps(part_reference_catalog, ensure_ascii=False, indent=2),
        "",
        "输出要求：",
        "- 仅输出一个严格 JSON 对象。",
        "- 输出文件语义是 scene_semantic.json。",
        "- 只定义“场景语义 + 叙事分镜 + 对象列表”。",
        "- 不要给 CompositeObject 写 graph（graph 在 llm_draw 阶段生成）。",
        "- 不要输出 markdown。",
        "- objects[].type 只能从“允许的顶层 object.type”里选。",
        "- part.type（如 Wall/Block/Pulley 等）只能用于 CompositeObject 的绘制语义提示，不能直接作为 objects[].type。",
        "- 地面/斜面/坡面语义必须指向 Wall；不要把 InclinedPlane 当作地面组件。",
        "",
        "CustomObject 专项规则：",
        "- 仅当现有组件和 CompositeObject.graph 无法表达时才使用 CustomObject。",
        "- CustomObject.params 必须包含：custom_role、draw_prompt、motion_prompt、codegen_request。",
        "- custom_role 只能是：new_component、special_motion、complex_effect。",
        "- codegen_request 必须包含：enabled（bool）、scope（object/motion/effect/hybrid）、intent（非空字符串）。",
        "- codegen_request.kind_hint 可选，若给出只能是：new_component/special_motion/complex_effect/hybrid/custom。",
        "- 可选：manim_api_hints（字符串数组）、motion_span_s_hint（正数秒）。",
    ]

    if compact_teaching is not None:
        lines.extend(
            [
                "",
                "teaching_plan（教学结构约束）：",
                json.dumps(compact_teaching, ensure_ascii=False, indent=2),
            ]
        )

    if compact_narrative is not None:
        lines.extend(
            [
                "",
                "narrative_plan（叙事节奏约束）：",
                json.dumps(compact_narrative, ensure_ascii=False, indent=2),
            ]
        )

    return "\n".join(lines)


def _build_repair_payload(
    *,
    problem: str,
    teaching_plan: dict[str, Any] | None,
    narrative_plan: dict[str, Any] | None,
    allowed_object_types: set[str],
    part_reference_catalog: list[dict[str, str]],
    raw_content: str,
    errors: list[str],
    round_index: int,
) -> str:
    top_level_allowed = [x for x in _TOP_LEVEL_OBJECT_TYPES if x in allowed_object_types]
    compact_teaching = _compact_teaching_plan(teaching_plan)
    compact_narrative = _compact_narrative_plan(narrative_plan)
    lines = [
        f"这是第 {round_index} 轮修复。请在最小改动下修复 scene_semantic.json。",
        "仅输出 JSON。",
        "",
        "校验错误：",
        _render_error_lines(errors),
        "",
        "题目：",
        problem.strip(),
        "",
        "当前错误内容：",
        raw_content.strip(),
        "",
        "允许的顶层 object.type：",
        json.dumps(top_level_allowed, ensure_ascii=False, indent=2),
        "",
        "CompositeObject part.type 参考清单（仅供语义提示，禁止作为 objects[].type）：",
        "（来源：llm_constraints/specs/components_catalog.json）",
        json.dumps(part_reference_catalog, ensure_ascii=False, indent=2),
        "",
        "硬约束：",
        "1) 根对象必须包含 version/scenes，可选 pedagogy_plan。",
        "2) 每个 scene 必须有 narrative_storyboard。",
        "3) narrative_storyboard.animation_steps 必须非空，且每步要有 targets + duration_s。",
        "4) 非最后 scene 必须有 bridge_to_next。",
        "5) CompositeObject 在本阶段不能写 graph。",
        "6) 若使用 CustomObject，params 必须包含 custom_role/draw_prompt/motion_prompt/codegen_request。",
        "7) custom_role 只能是 new_component/special_motion/complex_effect。",
        "8) codegen_request 必须包含 enabled/scope/intent，kind_hint 可选但需在允许值内。",
        "9) objects[].type 只能使用顶层 object.type 白名单。",
        "10) part.type 只能出现在 CompositeObject 的绘制语义提示，不得写入 objects[].type。",
        "11) 地面/斜面/坡面语义必须指向 Wall，不要把 InclinedPlane 当作地面组件。",
    ]

    if compact_teaching is not None:
        lines.extend(
            [
                "",
                "teaching_plan：",
                json.dumps(compact_teaching, ensure_ascii=False, indent=2),
            ]
        )

    if compact_narrative is not None:
        lines.extend(
            [
                "",
                "narrative_plan：",
                json.dumps(compact_narrative, ensure_ascii=False, indent=2),
            ]
        )

    lines.extend(["", "只输出修复后的 JSON。"])
    return "\n".join(lines)


def _parse_and_validate(content: str) -> tuple[dict[str, Any] | None, list[str]]:
    try:
        data = load_json_from_llm(content)
    except Exception as exc:  # noqa: BLE001
        return None, [f"JSON parse failed: {exc}"]

    try:
        model = SceneSemanticPlan.model_validate(data)
    except Exception as exc:  # noqa: BLE001
        return None, [f"scene_semantic schema invalid: {exc}"]

    custom_errors = _validate_custom_object_hints(model)
    if custom_errors:
        return None, custom_errors

    return model.model_dump(mode="json"), []


def main() -> int:
    parser = argparse.ArgumentParser(description="LLM2: generate scene_semantic.json")
    parser.add_argument("--case", default="cases/demo_001", help="Case directory, e.g. cases/demo_001")
    parser.add_argument("--problem", default=None, help="Optional problem file path (default: case/problem.md)")
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
    generate_llm_cfg = load_zhipu_stage_config("llm2", "generate", base_cfg=base_llm_cfg)
    continue_llm_cfg = load_zhipu_stage_config("llm2", "continue", base_cfg=base_llm_cfg)
    repair_llm_cfg = load_zhipu_stage_config("llm2", "repair", base_cfg=base_llm_cfg)

    case_dir = Path(args.case)
    problem_path = Path(args.problem) if args.problem else (case_dir / "problem.md")
    teaching_plan_path = Path(args.teaching_plan) if args.teaching_plan else (case_dir / "teaching_plan.json")
    narrative_plan_path = Path(args.narrative_plan) if args.narrative_plan else (case_dir / "narrative_plan.json")

    problem = problem_path.read_text(encoding="utf-8")
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
    part_reference_hints = _load_part_reference_hints()
    part_reference_catalog = _build_part_reference_catalog(
        allowed_object_types,
        part_reference_hints=part_reference_hints,
    )
    catalog_errors = _validate_part_reference_catalog(
        allowed_object_types=allowed_object_types,
        catalog=part_reference_catalog,
    )
    if catalog_errors:
        print("\n".join(catalog_errors), file=sys.stderr)
        return 2

    prompt = compose_prompt("llm2", context={"has_narrative_plan": narrative_plan is not None})
    system_prompt_path = case_dir / "llm2_system_prompt.txt"
    system_prompt_path.write_text(prompt.strip() + "\n", encoding="utf-8")

    user_payload = _build_user_payload(
        problem=problem,
        teaching_plan=teaching_plan,
        narrative_plan=narrative_plan,
        allowed_object_types=allowed_object_types,
        part_reference_catalog=part_reference_catalog,
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

    raw_path = case_dir / "llm2_raw.txt"
    raw_path.write_text(content.strip() + "\n", encoding="utf-8")
    _write_continuation_chunks(case_dir, "llm2_continue_raw", cont_chunks)

    validation_log: list[str] = []
    data, errors = _parse_and_validate(content)
    if errors:
        validation_log.append("[initial]")
        validation_log.extend(errors)
        validation_log.append("")

    errors_path = case_dir / "llm2_validation_errors.txt"
    if errors and args.no_repair:
        errors_path.write_text("\n".join(validation_log).strip() + "\n", encoding="utf-8")
        print(f"LLM2 output invalid. See: {raw_path} and {errors_path}", file=sys.stderr)
        return 2

    if errors:
        repair_prompt = load_prompt("json_repair.md")
        current_content = content
        repair_raw_path = case_dir / "llm2_repair_raw.txt"

        for round_index in range(1, max(1, args.repair_rounds) + 1):
            repair_payload = _build_repair_payload(
                problem=problem,
                teaching_plan=teaching_plan,
                narrative_plan=narrative_plan,
                allowed_object_types=allowed_object_types,
                part_reference_catalog=part_reference_catalog,
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
            (case_dir / f"llm2_repair_raw_round_{round_index}.txt").write_text(
                repaired.strip() + "\n", encoding="utf-8"
            )
            _write_continuation_chunks(case_dir, f"llm2_repair_continue_raw_r{round_index}", repair_cont_chunks)

            data, errors = _parse_and_validate(repaired)
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

    assert data is not None
    if errors_path.exists():
        errors_path.unlink()

    out_path = case_dir / "scene_semantic.json"
    out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(str(out_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())



