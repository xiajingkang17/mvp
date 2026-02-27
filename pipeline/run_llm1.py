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
from schema.teaching_plan_models import TeachingPlan


_CONTENT_ITEM_ENUM = [
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

_DERIVATION_STEP_TYPE_ENUM = ["equation", "compute", "reasoning", "diagram_note"]


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

    nodes = concept_tree.get("nodes")
    if not isinstance(nodes, list):
        nodes = []
    edges = concept_tree.get("edges")
    if not isinstance(edges, list):
        edges = []
    ordered = concept_tree.get("ordered_concepts")
    if not isinstance(ordered, list):
        ordered = []

    id_to_concept: dict[str, str] = {}
    foundation_concepts: list[str] = []
    for node in nodes:
        if not isinstance(node, dict):
            continue
        node_id = str(node.get("id", "")).strip()
        concept = str(node.get("concept", "")).strip()
        if not node_id or not concept:
            continue
        id_to_concept[node_id] = concept
        if bool(node.get("is_foundation")):
            foundation_concepts.append(concept)

    dependencies: dict[str, list[str]] = {}
    for edge in edges:
        if not isinstance(edge, dict):
            continue
        src_id = str(edge.get("from_id", "")).strip()
        dst_id = str(edge.get("to_id", "")).strip()
        src = id_to_concept.get(src_id)
        dst = id_to_concept.get(dst_id)
        if not src or not dst:
            continue
        dependencies.setdefault(src, [])
        if dst not in dependencies[src]:
            dependencies[src].append(dst)

    return {
        "analysis": {
            "core_concept": str(analysis_compact.get("core_concept", "")).strip(),
            "domain": str(analysis_compact.get("domain", "")).strip(),
            "level": str(analysis_compact.get("level", "")).strip(),
            "goal": str(analysis_compact.get("goal", "")).strip(),
        },
        "ordered_concepts": [str(x).strip() for x in ordered if str(x).strip()],
        "foundations": foundation_concepts,
        "dependencies": [
            {"concept": concept, "requires": prereqs} for concept, prereqs in dependencies.items()
        ],
    }


def _build_user_payload(problem: str, *, concept_tree: dict[str, Any] | None) -> str:
    lines = [
        "Problem statement:",
        problem.strip(),
        "",
        "Output requirement:",
        "- Output one strict JSON object only.",
        "- Follow the contract in the system prompt.",
        "- Do not output markdown.",
    ]

    compact_tree = _compact_concept_tree(concept_tree)
    if compact_tree is not None:
        lines.extend(
            [
                "",
                "concept_tree.json (from LLM0, treat as prerequisite contract):",
                json.dumps(compact_tree, ensure_ascii=False, indent=2),
                "",
                "Alignment rules:",
                "- Respect prerequisite-first order from ordered_concepts.",
                "- Do not teach dependent concepts before their prerequisites.",
                "- Ensure sub_questions progression can map back to this concept tree.",
                "- Preserve mathematical rigor: equations -> substitution -> numeric result -> sanity check.",
            ]
        )

    return "\n".join(lines)


def _build_repair_payload(
    *,
    problem: str,
    concept_tree: dict[str, Any] | None,
    raw_content: str,
    errors: list[str],
    round_index: int,
) -> str:
    lines = [
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
        json.dumps(_CONTENT_ITEM_ENUM, ensure_ascii=False),
        "",
        "Derivation step type enum:",
        json.dumps(_DERIVATION_STEP_TYPE_ENUM, ensure_ascii=False),
    ]

    compact_tree = _compact_concept_tree(concept_tree)
    if compact_tree is not None:
        lines.extend(
            [
                "",
                "concept_tree.json (from LLM0, keep teaching order aligned):",
                json.dumps(compact_tree, ensure_ascii=False, indent=2),
            ]
        )

    lines.extend(["", "Output only repaired JSON."])
    return "\n".join(lines)


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
    parser.add_argument(
        "--concept-tree",
        default=None,
        help="Optional concept_tree.json path (default: case/concept_tree.json if exists)",
    )
    parser.add_argument("--no-repair", action="store_true", help="Skip repair when parse/validation fails")
    parser.add_argument("--continue-rounds", type=int, default=2, help="Max continuation rounds for truncated JSON")
    parser.add_argument("--repair-rounds", type=int, default=2, help="Max validation-driven repair rounds")
    args = parser.parse_args()

    load_dotenv()
    base_llm_cfg = load_zhipu_config()
    generate_llm_cfg = load_zhipu_stage_config("llm1", "generate", base_cfg=base_llm_cfg)
    continue_llm_cfg = load_zhipu_stage_config("llm1", "continue", base_cfg=base_llm_cfg)
    repair_llm_cfg = load_zhipu_stage_config("llm1", "repair", base_cfg=base_llm_cfg)

    case_dir = Path(args.case)
    problem_path = Path(args.problem) if args.problem else (case_dir / "problem.md")
    concept_tree_path = Path(args.concept_tree) if args.concept_tree else (case_dir / "concept_tree.json")
    system_prompt_path = case_dir / "llm1_system_prompt.txt"

    problem = problem_path.read_text(encoding="utf-8")
    concept_tree: dict[str, Any] | None = None
    if concept_tree_path.exists():
        try:
            parsed = json.loads(concept_tree_path.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            print(f"Invalid concept_tree.json: {exc}", file=sys.stderr)
            return 2
        if isinstance(parsed, dict):
            concept_tree = parsed
    elif args.concept_tree:
        print(f"Missing specified concept tree file: {concept_tree_path}", file=sys.stderr)
        return 2

    prompt = compose_prompt("llm1")
    system_prompt_path.write_text(prompt.strip() + "\n", encoding="utf-8")
    user_payload = _build_user_payload(problem, concept_tree=concept_tree)

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
                concept_tree=concept_tree,
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
