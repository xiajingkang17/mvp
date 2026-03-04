from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in {None, ""}:
    MVP_ROOT = Path(__file__).resolve().parents[2]
    if str(MVP_ROOT) not in sys.path:
        sys.path.insert(0, str(MVP_ROOT))

from pipeline.cli_utils import read_requirement, write_text  # noqa: E402
from pipeline.mixed_workflow.run_mvp import (  # noqa: E402
    build_client,
    load_stage1_analysis,
    load_stage1_problem_solving,
    reset_case_outputs,
    stage_scene_plan,
)
from pipeline.run_layout import RunLayout  # noqa: E402


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="LLM2（scene_planner）：拆分并规划 scenes")
    p.add_argument("--run-dir", type=str, required=True, help="运行目录（需要包含 llm1 的 stage1 拆分输出）")
    p.add_argument("-r", "--requirement", type=str, default="")
    p.add_argument("--requirement-file", type=str, default="")
    p.add_argument("--analyst-json", type=str, default="", help="可选：指定旧版 stage1_analyst.json 路径")
    p.add_argument("--force", action="store_true", help="已废弃参数（兼容保留，不再使用）")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    run_dir = Path(args.run_dir)
    if not run_dir.exists():
        raise SystemExit(f"--run-dir 不存在: {run_dir}")
    layout = RunLayout.from_run_dir(run_dir)
    reset_case_outputs(layout, from_stage=2)

    requirement = read_requirement(
        requirement=args.requirement,
        requirement_file=args.requirement_file,
        run_dir=run_dir,
    )

    analyst_override = Path(args.analyst_json) if args.analyst_json else None
    if analyst_override is not None and not analyst_override.exists():
        raise SystemExit(f"缺少 analyst 输出: {analyst_override}（请先运行 run_llm1.py）")
    try:
        analysis = load_stage1_analysis(layout=layout, path=analyst_override)
        problem_solving = load_stage1_problem_solving(layout=layout)
    except FileNotFoundError as e:
        raise SystemExit(f"缺少 analyst 输出: {e}（请先运行 run_llm1.py）") from e

    client = build_client()
    system = client.load_stage_system_prompt("scene_planner")
    write_text(layout.llm2_system_prompt, system.strip() + "\n")

    stage_scene_plan(
        client,
        requirement=requirement,
        analysis=analysis,
        problem_solving=problem_solving,
        out_dir=layout.llm2_dir,
    )
    out_json = layout.stage2_json
    print(f"[LLM2] 输出: {out_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
