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
from schema.concept_tree_models import ConceptTree


_REQUIRED_ROOT_KEYS = {
    "analysis",
    "root_id",
    "nodes",
    "edges",
    "ordered_concepts",
    "explanation",
}


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
            "Required root keys (exactly):",
            json.dumps(sorted(_REQUIRED_ROOT_KEYS), ensure_ascii=False),
            "",
            "Allowed analysis.level:",
            json.dumps(["beginner", "intermediate", "advanced"], ensure_ascii=False),
            "",
            "Edge relation enum:",
            json.dumps(["requires"], ensure_ascii=False),
            "",
            "Output only repaired JSON.",
        ]
    )


def _validate_root_keys(data: Any) -> list[str]:
    if not isinstance(data, dict):
        return ["concept_tree root must be a JSON object"]

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
        model = ConceptTree.model_validate(data)
    except Exception as exc:  # noqa: BLE001
        return None, [f"concept_tree schema invalid: {exc}"]

    return model.model_dump(mode="json"), []


def main() -> int:
    parser = argparse.ArgumentParser(description="LLM0: generate concept_tree.json")
    parser.add_argument("--case", default="cases/demo_001", help="Case directory, e.g. cases/demo_001")
    parser.add_argument("--problem", default=None, help="Optional problem file path (default: case/problem.md)")
    parser.add_argument("--no-repair", action="store_true", help="Skip repair when parse/validation fails")
    parser.add_argument("--continue-rounds", type=int, default=2, help="Max continuation rounds for truncated JSON")
    parser.add_argument("--repair-rounds", type=int, default=2, help="Max validation-driven repair rounds")
    args = parser.parse_args()

    load_dotenv()
    base_llm_cfg = load_zhipu_config()
    generate_llm_cfg = load_zhipu_stage_config("llm0", "generate", base_cfg=base_llm_cfg)
    continue_llm_cfg = load_zhipu_stage_config("llm0", "continue", base_cfg=base_llm_cfg)
    repair_llm_cfg = load_zhipu_stage_config("llm0", "repair", base_cfg=base_llm_cfg)

    case_dir = Path(args.case)
    problem_path = Path(args.problem) if args.problem else (case_dir / "problem.md")
    system_prompt_path = case_dir / "llm0_system_prompt.txt"

    problem = problem_path.read_text(encoding="utf-8")
    prompt = compose_prompt("llm0")
    system_prompt_path.write_text(prompt.strip() + "\n", encoding="utf-8")
    user_payload = _build_user_payload(problem)

    content = chat_completion(
        [
            ChatMessage(role="system", content=prompt),
            ChatMessage(role="user", content=user_payload),
        ],
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

    raw_path = case_dir / "llm0_raw.txt"
    raw_path.write_text(content.strip() + "\n", encoding="utf-8")
    _write_continuation_chunks(case_dir, "llm0_continue_raw", cont_chunks)

    validation_log: list[str] = []
    data, errors = _parse_and_validate(content)
    if errors:
        validation_log.append("[initial]")
        validation_log.extend(errors)
        validation_log.append("")

    errors_path = case_dir / "llm0_validation_errors.txt"
    if errors and args.no_repair:
        errors_path.write_text("\n".join(validation_log).strip() + "\n", encoding="utf-8")
        print(f"LLM0 output parse/validation failed. See: {raw_path} and {errors_path}", file=sys.stderr)
        return 2

    if errors:
        repair_prompt = load_prompt("json_repair.md")
        current_content = content
        repair_raw_path = case_dir / "llm0_repair_raw.txt"

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
                ],
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
            (case_dir / f"llm0_repair_raw_round_{round_index}.txt").write_text(
                repaired.strip() + "\n", encoding="utf-8"
            )
            _write_continuation_chunks(case_dir, f"llm0_repair_continue_raw_r{round_index}", repair_cont_chunks)

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
                "LLM0 repair rounds finished but output is still invalid. "
                f"See: {raw_path}, {repair_raw_path}, {errors_path}",
                file=sys.stderr,
            )
            return 2

    assert data is not None
    if errors_path.exists():
        errors_path.unlink()

    concept_tree_path = case_dir / "concept_tree.json"
    concept_tree_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(str(concept_tree_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
