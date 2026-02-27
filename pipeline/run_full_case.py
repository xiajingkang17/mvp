from __future__ import annotations

import argparse
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


ROOT_DIR = Path(__file__).resolve().parents[1]

STEP_ORDER: tuple[str, ...] = (
    "llm0",
    "llm1",
    "llm_n",
    "llm2",
    "llm_codegen_pre",
    "llm_draw",
    "build_draft",
    "llm3",
    "build_plan",
    "llm_codegen",
    "validate",
)


@dataclass(frozen=True)
class StepSpec:
    name: str
    module: str


STEP_SPECS: dict[str, StepSpec] = {
    "llm0": StepSpec(name="llm0", module="pipeline.run_llm0"),
    "llm1": StepSpec(name="llm1", module="pipeline.run_llm1"),
    "llm_n": StepSpec(name="llm_n", module="pipeline.run_llm_n"),
    "llm2": StepSpec(name="llm2", module="pipeline.run_llm2"),
    "llm_codegen_pre": StepSpec(name="llm_codegen_pre", module="pipeline.run_llm_codegen"),
    "llm_draw": StepSpec(name="llm_draw", module="pipeline.run_llm_draw"),
    "build_draft": StepSpec(name="build_draft", module="pipeline.build_draft"),
    "llm3": StepSpec(name="llm3", module="pipeline.run_llm3"),
    "build_plan": StepSpec(name="build_plan", module="pipeline.build_plan"),
    "llm_codegen": StepSpec(name="llm_codegen", module="pipeline.run_llm_codegen"),
    "validate": StepSpec(name="validate", module="pipeline.validate_plan"),
}


def _normalize_step_name_list(raw_steps: Iterable[str]) -> set[str]:
    result: set[str] = set()
    for raw in raw_steps:
        step = str(raw).strip()
        if not step:
            continue
        if step not in STEP_SPECS:
            raise ValueError(f"Unknown step: {step}. Allowed: {', '.join(STEP_ORDER)}")
        result.add(step)
    return result


def _select_steps(*, from_step: str, to_step: str, skip_steps: set[str]) -> list[str]:
    if from_step not in STEP_SPECS:
        raise ValueError(f"Unknown --from-step: {from_step}")
    if to_step not in STEP_SPECS:
        raise ValueError(f"Unknown --to-step: {to_step}")

    start = STEP_ORDER.index(from_step)
    end = STEP_ORDER.index(to_step)
    if start > end:
        raise ValueError(f"--from-step ({from_step}) must be before --to-step ({to_step})")

    picked: list[str] = []
    for step in STEP_ORDER[start : end + 1]:
        if step in skip_steps:
            continue
        picked.append(step)
    return picked


def _build_command(
    *,
    python_bin: str,
    step: str,
    case_dir: Path,
    validate_autofix: bool,
    validate_write: bool,
) -> list[str]:
    spec = STEP_SPECS[step]
    if step == "validate":
        plan_path = case_dir / "scene_plan.json"
        cmd = [python_bin, "-m", spec.module, str(plan_path)]
        if validate_autofix:
            cmd.append("--autofix")
        if validate_write:
            cmd.append("--write")
        return cmd

    if step == "llm_codegen_pre":
        return [
            python_bin,
            "-m",
            spec.module,
            "--case",
            str(case_dir),
            "--targets-from",
            "semantic",
            "--skip-apply-plan",
        ]

    return [python_bin, "-m", spec.module, "--case", str(case_dir)]


def _print_command(step: str, cmd: list[str]) -> None:
    rendered = " ".join(shlex.quote(part) for part in cmd)
    print(f"[{step}] {rendered}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run the full case pipeline:\n"
            "llm0 -> llm1 -> llm_n -> llm2 -> llm_codegen_pre -> llm_draw -> build_draft -> llm3 -> build_plan -> llm_codegen -> validate"
        )
    )
    parser.add_argument("--case", default="cases/demo_001", help="Case directory, e.g. cases/demo_001")
    parser.add_argument("--from-step", default=STEP_ORDER[0], choices=STEP_ORDER, help="First step to run")
    parser.add_argument("--to-step", default=STEP_ORDER[-1], choices=STEP_ORDER, help="Last step to run")
    parser.add_argument(
        "--skip",
        action="append",
        default=[],
        metavar="STEP",
        help=f"Step to skip; can repeat. Choices: {', '.join(STEP_ORDER)}",
    )
    parser.add_argument("--python", default=sys.executable, help="Python executable used to run sub-commands")
    parser.add_argument("--dry-run", action="store_true", help="Print commands only; do not execute")
    parser.add_argument("--keep-going", action="store_true", help="Continue even if one step fails")
    parser.add_argument(
        "--validate-autofix",
        action="store_true",
        help="Pass --autofix to validate step",
    )
    parser.add_argument(
        "--validate-write",
        action="store_true",
        help="Pass --write to validate step",
    )
    args = parser.parse_args(argv)

    case_dir = Path(args.case)
    if not case_dir.is_absolute():
        case_dir = (ROOT_DIR / case_dir).resolve()
    if not case_dir.exists():
        print(f"Case directory not found: {case_dir}", file=sys.stderr)
        return 2

    try:
        skip_steps = _normalize_step_name_list(args.skip)
        selected = _select_steps(from_step=args.from_step, to_step=args.to_step, skip_steps=skip_steps)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if not selected:
        print("No steps selected.", file=sys.stderr)
        return 2

    print("Pipeline steps:")
    for step in selected:
        print(f"- {step}")

    failed_steps: list[tuple[str, int]] = []

    for step in selected:
        cmd = _build_command(
            python_bin=str(args.python),
            step=step,
            case_dir=case_dir,
            validate_autofix=bool(args.validate_autofix),
            validate_write=bool(args.validate_write),
        )
        _print_command(step, cmd)
        if args.dry_run:
            continue

        result = subprocess.run(cmd, cwd=str(ROOT_DIR), check=False)
        if result.returncode == 0:
            continue

        if args.keep_going:
            print(f"[{step}] failed with exit code {result.returncode}; keep going")
            failed_steps.append((step, int(result.returncode)))
            continue

        print(f"[{step}] failed with exit code {result.returncode}", file=sys.stderr)
        return result.returncode

    if failed_steps:
        failed = ", ".join(f"{name}({code})" for name, code in failed_steps)
        print(f"Completed with failures: {failed}", file=sys.stderr)
        return failed_steps[-1][1]

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
