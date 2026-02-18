from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from pipeline.env import load_dotenv
from pipeline.json_utils import load_json_from_llm
from pipeline.llm.types import ChatMessage
from pipeline.llm.zhipu import chat_completion
from pipeline.llm_continuation import continue_json_output
from pipeline.prompting import load_prompt
from schema.teaching_plan_models import TeachingPlan


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


def _build_user_payload(problem: str) -> str:
    return "\n".join(
        [
            "Problem statement:",
            problem.strip(),
            "",
            "Output requirement:",
            "- Output one strict JSON object only.",
            "- Follow the contract in the system prompt.",
            "- Do not output markdown.",
        ]
    )


def _build_repair_payload(*, problem: str, raw_content: str, errors: list[str], round_index: int) -> str:
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
            "Invalid raw content:",
            raw_content.strip(),
            "",
            "Required root keys:",
            json.dumps(["explanation_full", "global_symbols", "sub_questions"], ensure_ascii=False),
            "",
            "Scene content item enum:",
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
            "Output only repaired JSON.",
        ]
    )


def _parse_and_validate(content: str) -> tuple[dict[str, Any] | None, list[str]]:
    try:
        data = load_json_from_llm(content)
    except Exception as exc:  # noqa: BLE001
        return None, [f"JSON parse failed: {exc}"]

    try:
        model = TeachingPlan.model_validate(data)
    except Exception as exc:  # noqa: BLE001
        return None, [f"teaching_plan schema invalid: {exc}"]

    return model.model_dump(mode="json"), []


def main() -> int:
    parser = argparse.ArgumentParser(description="LLM1: generate teaching_plan.json")
    parser.add_argument("--case", default="cases/demo_001", help="Case directory, e.g. cases/demo_001")
    parser.add_argument("--problem", default=None, help="Optional problem file path (default: case/problem.md)")
    parser.add_argument("--no-repair", action="store_true", help="Skip repair when parse/validation fails")
    parser.add_argument("--continue-rounds", type=int, default=2, help="Max continuation rounds for truncated JSON")
    parser.add_argument("--repair-rounds", type=int, default=2, help="Max validation-driven repair rounds")
    args = parser.parse_args()

    load_dotenv()

    case_dir = Path(args.case)
    problem_path = Path(args.problem) if args.problem else (case_dir / "problem.md")

    problem = problem_path.read_text(encoding="utf-8")
    prompt = load_prompt("llm1_teaching_plan.md")
    user_payload = _build_user_payload(problem)

    content = chat_completion(
        [
            ChatMessage(role="system", content=prompt),
            ChatMessage(role="user", content=user_payload),
        ]
    )
    content, cont_chunks = continue_json_output(
        content,
        system_prompt=prompt,
        user_payload=user_payload,
        parse_fn=load_json_from_llm,
        max_rounds=args.continue_rounds,
    )

    raw_path = case_dir / "llm1_raw.txt"
    raw_path.write_text(content.strip() + "\n", encoding="utf-8")
    _write_continuation_chunks(case_dir, "llm1_continue_raw", cont_chunks)

    validation_log: list[str] = []
    data, errors = _parse_and_validate(content)
    if errors:
        validation_log.append("[initial]")
        validation_log.extend(errors)
        validation_log.append("")

    errors_path = case_dir / "llm1_validation_errors.txt"
    if errors and args.no_repair:
        errors_path.write_text("\n".join(validation_log).strip() + "\n", encoding="utf-8")
        print(f"LLM1 output parse/validation failed. See: {raw_path} and {errors_path}", file=sys.stderr)
        return 2

    if errors:
        repair_prompt = load_prompt("json_repair.md")
        current_content = content
        repair_raw_path = case_dir / "llm1_repair_raw.txt"

        for round_index in range(1, max(1, args.repair_rounds) + 1):
            repair_payload = _build_repair_payload(
                problem=problem,
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
            (case_dir / f"llm1_repair_raw_round_{round_index}.txt").write_text(
                repaired.strip() + "\n", encoding="utf-8"
            )
            _write_continuation_chunks(case_dir, f"llm1_repair_continue_raw_r{round_index}", repair_cont_chunks)

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
                "LLM1 repair rounds finished but output is still invalid. "
                f"See: {raw_path}, {repair_raw_path}, {errors_path}",
                file=sys.stderr,
            )
            return 2

    assert data is not None
    if errors_path.exists():
        errors_path.unlink()

    teaching_plan_path = case_dir / "teaching_plan.json"
    teaching_plan_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(str(teaching_plan_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
