from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Literal

if __package__ in {None, ""}:
    MVP_ROOT = Path(__file__).resolve().parents[2]
    if str(MVP_ROOT) not in sys.path:
        sys.path.insert(0, str(MVP_ROOT))

from pipeline.cli_utils import ensure_run_dir, read_requirement, write_text  # noqa: E402
from pipeline.run_layout import RunLayout  # noqa: E402
from pipeline.zhipu_workflow.run_mvp import build_client, reset_case_outputs, stage_analyst  # noqa: E402


def parse_args(default_llm1_provider: Literal["zhipu", "anthropic", "kimi"] = "zhipu") -> argparse.Namespace:
    p = argparse.ArgumentParser(description="LLM1（analyst）：分析 + 前置知识探索")
    p.add_argument("-r", "--requirement", type=str, default="")
    p.add_argument("--requirement-file", type=str, default="")
    p.add_argument("--run-dir", type=str, default="", help="运行目录（不传则自动创建）")
    p.add_argument(
        "--llm1-provider",
        choices=["anthropic", "zhipu", "kimi"],
        default=default_llm1_provider,
        help="llm1 analyst 使用的 provider",
    )
    p.add_argument("--force", action="store_true", help="已废弃参数（兼容保留，不再使用）")
    return p.parse_args()


def main(default_llm1_provider: Literal["zhipu", "anthropic", "kimi"] = "zhipu") -> int:
    args = parse_args(default_llm1_provider)

    run_dir_hint = Path(args.run_dir) if args.run_dir else None
    requirement = read_requirement(
        requirement=args.requirement,
        requirement_file=args.requirement_file,
        run_dir=run_dir_hint,
    )

    run_dir = ensure_run_dir(
        requirement=requirement,
        run_dir=args.run_dir,
        requirement_file=args.requirement_file,
    )
    layout = RunLayout.from_run_dir(run_dir)
    reset_case_outputs(layout, from_stage=1)
    print(f"[LLM1] 运行目录: {run_dir}")

    write_text(layout.requirement_txt, requirement.strip() + "\n")

    client = build_client(llm1_provider=args.llm1_provider)
    system = client.load_stage_system_prompt("analyst")
    write_text(layout.llm1_system_prompt, system.strip() + "\n")

    stage_analyst(client, requirement=requirement, out_dir=layout.llm1_dir)
    print(f"[LLM1] provider: {args.llm1_provider}")
    print(f"[LLM1] 输出: {layout.stage1_analysis_json}")
    print(f"[LLM1] 输出: {layout.stage1_problem_solving_json}")
    print(f"[LLM1] 输出: {layout.stage1_drawing_brief_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
