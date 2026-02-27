from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from pipeline.env import load_dotenv
from pipeline.json_utils import load_json_from_llm
from pipeline.llm.types import ChatMessage
from pipeline.llm.zhipu import chat_completion, load_zhipu_config, load_zhipu_stage_config
from pipeline.llm_continuation import continue_json_output
from pipeline.prompting import compose_prompt, load_prompt
from schema.narrative_plan_models import NarrativePlan


_REQUIRED_ROOT_KEYS = {
    "analysis",
    "global_arc",
    "ordered_concepts",
    "segments",
    "style_guide",
    "explanation",
}

_SCENE_FOCUS_ENUM = [
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
]


def _write_continuation_chunks(case_dir: Path, stem: str, chunks: list[str]) -> None:
    for idx, chunk in enumerate(chunks, start=1):
        (case_dir / f"{stem}_{idx}.txt").write_text(chunk.strip() + "\n", encoding="utf-8")


def _render_error_lines(errors: list[str], *, limit: int = 40) -> str:
    if not errors:
        return "(no validation errors)"
    lines = [f"- {err}" for err in errors[:limit]]
    if len(errors) > limit:
        lines.append(f"- ... and {len(errors) - limit} more errors")
    return "\n".join(lines)


def _compact_concept_tree(concept_tree: Any) -> dict[str, Any] | None:
    if not isinstance(concept_tree, dict):
        return None

    analysis = concept_tree.get("analysis")
    analysis_compact = analysis if isinstance(analysis, dict) else {}
    ordered = concept_tree.get("ordered_concepts")
    if not isinstance(ordered, list):
        ordered = []

    return {
        "analysis": {
            "core_concept": str(analysis_compact.get("core_concept", "")).strip(),
            "domain": str(analysis_compact.get("domain", "")).strip(),
            "level": str(analysis_compact.get("level", "")).strip(),
            "goal": str(analysis_compact.get("goal", "")).strip(),
        },
        "ordered_concepts": [str(x).strip() for x in ordered if str(x).strip()],
    }


def _compact_teaching_plan(teaching_plan: Any) -> dict[str, Any] | None:
    if not isinstance(teaching_plan, dict):
        return None

    sub_questions: list[dict[str, Any]] = []
    for item in teaching_plan.get("sub_questions") or []:
        if not isinstance(item, dict):
            continue
        sub_questions.append(
            {
                "id": str(item.get("id", "")).strip(),
                "goal": str(item.get("goal", "")).strip(),
                "method_choice": item.get("method_choice") if isinstance(item.get("method_choice"), dict) else {},
                "result": item.get("result") if isinstance(item.get("result"), dict) else {},
                "scene_packets": item.get("scene_packets") if isinstance(item.get("scene_packets"), list) else [],
            }
        )

    return {
        "global_symbols": teaching_plan.get("global_symbols") if isinstance(teaching_plan.get("global_symbols"), list) else [],
        "sub_questions": sub_questions,
    }


def _build_user_payload(
    *,
    problem: str,
    concept_tree: dict[str, Any],
    teaching_plan: dict[str, Any],
) -> str:
    compact_tree = _compact_concept_tree(concept_tree)
    compact_plan = _compact_teaching_plan(teaching_plan)
    return "\n".join(
        [
            "Problem statement:",
            problem.strip(),
            "",
            "concept_tree.json (from LLM0):",
            json.dumps(compact_tree, ensure_ascii=False, indent=2) if compact_tree is not None else "{}",
            "",
            "teaching_plan.json (from LLM1):",
            json.dumps(compact_plan, ensure_ascii=False, indent=2) if compact_plan is not None else "{}",
            "",
            "Output requirement:",
            "- Output one strict JSON object only.",
            "- Follow the contract in the system prompt.",
            "- Do not output markdown.",
        ]
    )


def _build_repair_payload(
    *,
    problem: str,
    concept_tree: dict[str, Any],
    teaching_plan: dict[str, Any],
    raw_content: str,
    errors: list[str],
    round_index: int,
) -> str:
    compact_tree = _compact_concept_tree(concept_tree)
    compact_plan = _compact_teaching_plan(teaching_plan)
    return "\n".join(
        [
            f"This is repair round {round_index}. Fix the JSON with minimal edits.",
            "Output JSON only.",
            "",
            "Validation errors:",
            _render_error_lines(errors),
            "",
            "Problem statement:",
            problem.strip(),
            "",
            "concept_tree.json:",
            json.dumps(compact_tree, ensure_ascii=False, indent=2) if compact_tree is not None else "{}",
            "",
            "teaching_plan.json:",
            json.dumps(compact_plan, ensure_ascii=False, indent=2) if compact_plan is not None else "{}",
            "",
            "Invalid raw content:",
            raw_content.strip(),
            "",
            "Required root keys (exactly):",
            json.dumps(sorted(_REQUIRED_ROOT_KEYS), ensure_ascii=False),
            "",
            "Scene focus enum:",
            json.dumps(_SCENE_FOCUS_ENUM, ensure_ascii=False),
            "",
            "Output only repaired JSON.",
        ]
    )


def _validate_root_keys(data: Any) -> list[str]:
    if not isinstance(data, dict):
        return ["narrative_plan root must be a JSON object"]
    actual_keys = set(data.keys())
    if actual_keys == _REQUIRED_ROOT_KEYS:
        return []

    missing = sorted(_REQUIRED_ROOT_KEYS - actual_keys)
    extra = sorted(actual_keys - _REQUIRED_ROOT_KEYS)
    errors: list[str] = []
    if missing:
        errors.append(f"Missing root keys: {missing}")
    if extra:
        errors.append(f"Unexpected root keys: {extra}")
    return errors


def _parse_and_validate(content: str) -> tuple[dict[str, Any] | None, list[str]]:
    try:
        data = load_json_from_llm(content)
    except Exception as exc:  # noqa: BLE001
        return None, [f"JSON parse failed: {exc}"]

    root_key_errors = _validate_root_keys(data)
    if root_key_errors:
        return None, root_key_errors

    try:
        model = NarrativePlan.model_validate(data)
    except Exception as exc:  # noqa: BLE001
        return None, [f"narrative_plan schema invalid: {exc}"]
    return model.model_dump(mode="json"), []


def _render_narrative_prompt(data: dict[str, Any]) -> str:
    lines: list[str] = []
    analysis = data.get("analysis")
    if isinstance(analysis, dict):
        target = str(analysis.get("target_concept", "")).strip()
        goal = str(analysis.get("narrative_goal", "")).strip()
        if target:
            lines.append(f"# Narrative Prompt: {target}")
            lines.append("")
        if goal:
            lines.append(f"Goal: {goal}")
            lines.append("")

    global_arc = str(data.get("global_arc", "")).strip()
    if global_arc:
        lines.append("## Global Arc")
        lines.append(global_arc)
        lines.append("")

    segments = data.get("segments")
    if isinstance(segments, list):
        for idx, seg in enumerate(segments, start=1):
            if not isinstance(seg, dict):
                continue
            seg_id = str(seg.get("id", "")).strip() or f"N{idx}"
            title = str(seg.get("title", "")).strip()
            concept_ref = str(seg.get("concept_ref", "")).strip()
            narration = str(seg.get("narration", "")).strip()
            visual_intent = str(seg.get("visual_intent", "")).strip()
            transition_hook = str(seg.get("transition_hook", "")).strip()
            scene_focus = str(seg.get("scene_focus", "")).strip()
            duration = seg.get("duration_hint_s")
            equations = seg.get("key_equations")
            if not isinstance(equations, list):
                equations = []

            header = f"## {idx}. {seg_id}"
            if title:
                header += f" - {title}"
            lines.append(header)
            if concept_ref:
                lines.append(f"Concept: {concept_ref}")
            if scene_focus:
                lines.append(f"Focus: {scene_focus}")
            if isinstance(duration, int):
                lines.append(f"Duration: {duration}s")
            if equations:
                lines.append("Key Equations:")
                for eq in equations:
                    eq_text = str(eq).strip()
                    if eq_text:
                        lines.append(f"- {eq_text}")
            if narration:
                lines.append("Narration:")
                lines.append(narration)
            if visual_intent:
                lines.append("Visual Intent:")
                lines.append(visual_intent)
            if transition_hook:
                lines.append("Transition Hook:")
                lines.append(transition_hook)
            lines.append("")

    return "\n".join(lines).strip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="LLM_N: generate narrative_plan.json")
    parser.add_argument("--case", default="cases/demo_001", help="Case directory, e.g. cases/demo_001")
    parser.add_argument("--problem", default=None, help="Optional problem file path (default: case/problem.md)")
    parser.add_argument(
        "--concept-tree",
        default=None,
        help="Optional concept_tree.json path (default: case/concept_tree.json)",
    )
    parser.add_argument(
        "--teaching-plan",
        default=None,
        help="Optional teaching_plan.json path (default: case/teaching_plan.json)",
    )
    parser.add_argument("--no-repair", action="store_true", help="Skip repair when parse/validation fails")
    parser.add_argument("--continue-rounds", type=int, default=2, help="Max continuation rounds for truncated JSON")
    parser.add_argument("--repair-rounds", type=int, default=2, help="Max validation-driven repair rounds")
    args = parser.parse_args()

    load_dotenv()
    base_llm_cfg = load_zhipu_config()
    generate_llm_cfg = load_zhipu_stage_config("llm_n", "generate", base_cfg=base_llm_cfg)
    continue_llm_cfg = load_zhipu_stage_config("llm_n", "continue", base_cfg=base_llm_cfg)
    repair_llm_cfg = load_zhipu_stage_config("llm_n", "repair", base_cfg=base_llm_cfg)

    case_dir = Path(args.case)
    problem_path = Path(args.problem) if args.problem else (case_dir / "problem.md")
    concept_tree_path = Path(args.concept_tree) if args.concept_tree else (case_dir / "concept_tree.json")
    teaching_plan_path = Path(args.teaching_plan) if args.teaching_plan else (case_dir / "teaching_plan.json")
    system_prompt_path = case_dir / "llm_n_system_prompt.txt"

    if not concept_tree_path.exists():
        print(f"Missing required input for LLM_N: {concept_tree_path}", file=sys.stderr)
        return 2
    if not teaching_plan_path.exists():
        print(f"Missing required input for LLM_N: {teaching_plan_path}", file=sys.stderr)
        return 2

    problem = problem_path.read_text(encoding="utf-8")
    try:
        concept_tree = json.loads(concept_tree_path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        print(f"Invalid concept_tree.json: {exc}", file=sys.stderr)
        return 2
    try:
        teaching_plan = json.loads(teaching_plan_path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        print(f"Invalid teaching_plan.json: {exc}", file=sys.stderr)
        return 2

    prompt = compose_prompt("llm_n")
    system_prompt_path.write_text(prompt.strip() + "\n", encoding="utf-8")
    user_payload = _build_user_payload(problem=problem, concept_tree=concept_tree, teaching_plan=teaching_plan)
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

    raw_path = case_dir / "llm_n_raw.txt"
    raw_path.write_text(content.strip() + "\n", encoding="utf-8")
    _write_continuation_chunks(case_dir, "llm_n_continue_raw", cont_chunks)

    validation_log: list[str] = []
    data, errors = _parse_and_validate(content)
    if errors:
        validation_log.append("[initial]")
        validation_log.extend(errors)
        validation_log.append("")

    errors_path = case_dir / "llm_n_validation_errors.txt"
    if errors and args.no_repair:
        errors_path.write_text("\n".join(validation_log).strip() + "\n", encoding="utf-8")
        print(f"LLM_N output parse/validation failed. See: {raw_path} and {errors_path}", file=sys.stderr)
        return 2

    if errors:
        repair_prompt = load_prompt("json_repair.md")
        current_content = content
        repair_raw_path = case_dir / "llm_n_repair_raw.txt"

        for round_index in range(1, max(1, args.repair_rounds) + 1):
            repair_payload = _build_repair_payload(
                problem=problem,
                concept_tree=concept_tree,
                teaching_plan=teaching_plan,
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
            (case_dir / f"llm_n_repair_raw_round_{round_index}.txt").write_text(
                repaired.strip() + "\n", encoding="utf-8"
            )
            _write_continuation_chunks(case_dir, f"llm_n_repair_continue_raw_r{round_index}", repair_cont_chunks)

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
                "LLM_N repair rounds finished but output is still invalid. "
                f"See: {raw_path}, {repair_raw_path}, {errors_path}",
                file=sys.stderr,
            )
            return 2

    assert data is not None
    if errors_path.exists():
        errors_path.unlink()

    narrative_plan_path = case_dir / "narrative_plan.json"
    narrative_plan_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (case_dir / "narrative_prompt.txt").write_text(_render_narrative_prompt(data), encoding="utf-8")

    print(str(narrative_plan_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
