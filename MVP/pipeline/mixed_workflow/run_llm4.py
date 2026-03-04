from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Literal

if __package__ in {None, ""}:
    MVP_ROOT = Path(__file__).resolve().parents[2]
    if str(MVP_ROOT) not in sys.path:
        sys.path.insert(0, str(MVP_ROOT))

from pipeline.cli_utils import load_json, write_text  # noqa: E402
from pipeline.mixed_workflow.run_mvp import (  # noqa: E402
    assemble_existing_llm4_fragments,
    build_client,
    load_stage35_layouts,
    load_stage1_problem_solving,
    load_stage1_drawing_brief,
    reset_case_outputs,
    stage_codegen_video,
    stage_render_fix_loop,
)
from pipeline.run_layout import RunLayout  # noqa: E402


def parse_args(default_llm4_provider: Literal["zhipu", "anthropic", "kimi"] = "anthropic") -> argparse.Namespace:
    p = argparse.ArgumentParser(description="LLM4：batch codegen，一次生成整片 scene/motion 片段，再由程序装配 scene.py")
    p.add_argument("--run-dir", type=str, required=True, help="运行目录（需要 llm1/llm2/llm3 输出）")
    p.add_argument("--scene-id", type=str, default="", help="可选：只把指定 scene_id 整合进单文件（用于调试）")
    p.add_argument(
        "--llm4-provider",
        choices=["anthropic", "zhipu", "kimi"],
        default=default_llm4_provider,
        help="llm4 四个 codegen 子阶段使用的 provider",
    )
    p.add_argument("--force", action="store_true", help="已废弃参数（兼容保留，不再使用）")
    p.add_argument("--quality", choices=["l", "m", "h"], default="l", help="manim 渲染质量：l 最快")
    p.add_argument("--render-timeout-s", type=int, default=300, help="单个渲染任务超时（秒）")
    p.add_argument("--max-fix-rounds", type=int, default=5, help="渲染失败时的最大自动修复轮数")
    p.add_argument("--no-render", action="store_true", help="只生成代码，不执行 manim 渲染")
    p.add_argument("--assemble-only", action="store_true", help="只读取现有 llm4 分段文件并重新装配 scene.py")
    p.add_argument("--no-auto-review", action="store_true", help="已废弃参数（兼容保留，不再使用）")
    p.add_argument("--max-static-fix-rounds", type=int, default=3, help="已废弃参数（兼容保留，不再使用）")
    return p.parse_args()


def _filter_scene_designs(payload: Any, *, scene_id: str) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {"video_title": "", "scenes": []}

    wanted = scene_id.strip()
    if not wanted:
        return payload

    scenes = payload.get("scenes") or []
    if not isinstance(scenes, list):
        scenes = []
    filtered = [
        sc
        for sc in scenes
        if isinstance(sc, dict) and str(sc.get("scene_id") or "").strip() == wanted
    ]
    return {"video_title": str(payload.get("video_title") or "").strip(), "scenes": filtered}


def _llm4_dir_name(provider: Literal["zhipu", "anthropic", "kimi"]) -> str:
    if provider == "anthropic":
        return "llm4_claude"
    if provider == "kimi":
        return "llm4_kimi"
    return "llm4_zhipu"


def main(default_llm4_provider: Literal["zhipu", "anthropic", "kimi"] = "anthropic") -> int:
    args = parse_args(default_llm4_provider)
    run_dir = Path(args.run_dir)
    if not run_dir.exists():
        raise SystemExit(f"--run-dir 不存在: {run_dir}")
    layout = RunLayout.from_run_dir(run_dir, llm4_dir_name=_llm4_dir_name(args.llm4_provider))
    if not args.assemble_only:
        reset_case_outputs(layout, from_stage=4)

    plan_path = layout.stage2_json
    stage3_path = layout.stage3_json
    stage35_path = layout.stage35_json
    if not plan_path.exists():
        legacy = run_dir / "stage2_scene_plan.json"
        if legacy.exists():
            plan_path = legacy
    if not stage3_path.exists():
        legacy = run_dir / "stage3_scene_designs.json"
        if legacy.exists():
            stage3_path = legacy
    if not stage35_path.exists():
        legacy = run_dir / "stage35_scene_layouts.json"
        if legacy.exists():
            stage35_path = legacy
    if not plan_path.exists():
        raise SystemExit(f"缺少: {plan_path}（请先运行 run_llm2.py）")
    if not stage3_path.exists():
        raise SystemExit(f"缺少: {stage3_path}（请先运行 run_llm3.py）")

    out_py = layout.llm4_scene_py

    plan = load_json(plan_path)
    scene_designs = _filter_scene_designs(load_json(stage3_path), scene_id=args.scene_id)
    scene_layouts = _filter_scene_designs(
        load_stage35_layouts(layout=layout, scene_designs=scene_designs),
        scene_id=args.scene_id,
    )
    if not (scene_designs.get("scenes") or []):
        raise SystemExit("scene_designs 为空：请检查 stage3_scene_designs.json 或 --scene-id")

    if args.assemble_only:
        class_name, code = assemble_existing_llm4_fragments(out_dir=layout.llm4_dir)
    else:
        try:
            stage1_problem_solving = load_stage1_problem_solving(layout=layout)
            stage1_drawing_brief = load_stage1_drawing_brief(layout=layout)
        except FileNotFoundError as e:
            raise SystemExit(f"缺少 llm1 输出: {e}（请先运行 run_llm1.py）") from e

        client = build_client(llm4_provider=args.llm4_provider)
        class_name, code = stage_codegen_video(
            client,
            stage1_problem_solving=stage1_problem_solving,
            stage1_drawing_brief=stage1_drawing_brief,
            plan=plan,
            scene_designs=scene_designs,
            scene_layouts=scene_layouts,
            out_dir=layout.llm4_dir,
        )
    write_text(out_py, code)
    write_text(layout.exported_scene_py, code)
    write_text(
        layout.stage4_meta,
        json.dumps(
            {
                "class_name": class_name,
                "codegen_mode": "assemble_only" if args.assemble_only else "batch_llm4",
                "provider": args.llm4_provider,
                "sub_stages": ["framework", "batch_codegen", "assemble"],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )

    if args.no_render:
        print(f"[LLM4] 输出: {out_py}（class_name={class_name}）")
        return 0

    client = build_client(llm4_provider=args.llm4_provider)
    class_name, ok, mp4_path, last_err, _last_attempt = stage_render_fix_loop(
        client,
        class_name=class_name,
        py_file=out_py,
        layout=layout,
        quality=args.quality,
        render_timeout_s=int(args.render_timeout_s),
        max_fix_rounds=int(args.max_fix_rounds),
    )
    if not ok:
        write_text(run_dir / "FAILED.txt", f"渲染失败：达到最大修复轮数 {args.max_fix_rounds}\n\n{last_err}")
        raise SystemExit(f"渲染失败：达到最大修复轮数 {args.max_fix_rounds}")

    print(f"[LLM4] 输出: {out_py}（class_name={class_name}），渲染成功: {mp4_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
