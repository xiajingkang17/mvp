from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Literal

if __package__ in {None, ""}:
    MVP_ROOT = Path(__file__).resolve().parents[2]
    if str(MVP_ROOT) not in sys.path:
        sys.path.insert(0, str(MVP_ROOT))

from pipeline.cli_utils import load_json, read_requirement, write_text  # noqa: E402
from pipeline.run_layout import RunLayout  # noqa: E402
from pipeline.zhipu_workflow.run_mvp import (  # noqa: E402
    build_client,
    load_stage1_drawing_brief,
    reset_case_outputs,
    stage_scene_layouts,
)


def parse_args(default_llm35_provider: Literal["zhipu", "anthropic", "kimi"] = "zhipu") -> argparse.Namespace:
    p = argparse.ArgumentParser(description="LLM3.5（layout_designer）：按整片 scenes 生成布局合同")
    p.add_argument("--run-dir", type=str, required=True, help="运行目录（需要 llm1/llm2/llm3 输出）")
    p.add_argument(
        "--llm35-provider",
        choices=["anthropic", "zhipu", "kimi"],
        default=default_llm35_provider,
        help="llm3.5 layout_designer 使用的 provider",
    )
    return p.parse_args()


def main(default_llm35_provider: Literal["zhipu", "anthropic", "kimi"] = "zhipu") -> int:
    args = parse_args(default_llm35_provider)
    run_dir = Path(args.run_dir)
    if not run_dir.exists():
        raise SystemExit(f"--run-dir 不存在: {run_dir}")

    layout = RunLayout.from_run_dir(run_dir)
    reset_case_outputs(layout, from_stage=35)

    requirement = read_requirement(run_dir=run_dir)

    plan_path = layout.stage2_json
    stage3_path = layout.stage3_json
    if not plan_path.exists():
        legacy = run_dir / "stage2_scene_plan.json"
        if legacy.exists():
            plan_path = legacy
    if not stage3_path.exists():
        legacy = run_dir / "stage3_scene_designs.json"
        if legacy.exists():
            stage3_path = legacy

    if not plan_path.exists():
        raise SystemExit(f"缺少: {plan_path}（请先运行 run_llm2.py）")
    if not stage3_path.exists():
        raise SystemExit(f"缺少: {stage3_path}（请先运行 run_llm3.py）")

    try:
        drawing_brief = load_stage1_drawing_brief(layout=layout)
    except FileNotFoundError as e:
        raise SystemExit(f"缺少 llm1 输出: {e}（请先运行 run_llm1.py）") from e

    plan = load_json(plan_path)
    scene_designs = load_json(stage3_path)

    client = build_client(llm35_provider=args.llm35_provider)
    system = client.load_stage_system_prompt("layout_designer")
    write_text(layout.llm35_system_prompt, system.strip() + "\n")

    payload = stage_scene_layouts(
        client,
        requirement=requirement,
        drawing_brief=drawing_brief,
        plan=plan,
        scene_designs=scene_designs,
        out_dir=layout.llm35_dir,
    )
    print(f"[LLM3.5] provider: {args.llm35_provider}")
    print(f"[LLM3.5] 完成: {len(payload.get('scenes') or [])} 个。输出: {layout.stage35_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
