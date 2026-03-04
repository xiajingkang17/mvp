from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

if __package__ in {None, ""}:
    MVP_ROOT = Path(__file__).resolve().parents[2]
    if str(MVP_ROOT) not in sys.path:
        sys.path.insert(0, str(MVP_ROOT))

    from pipeline.run_layout import RunLayout  # noqa: E402
    from pipeline.mixed_workflow.common import (  # noqa: E402
        RUNS_DIR,
        _slugify,
        _split_analyst_payload,
        _write_text,
        assemble_existing_llm4_fragments,
        build_client,
        load_stage1_analysis,
        load_stage1_drawing_brief,
        load_stage1_problem_solving,
        load_stage35_layouts,
        reset_case_outputs,
    )
    from pipeline.mixed_workflow.stage1_analyst import stage_analyst  # noqa: E402
    from pipeline.mixed_workflow.stage2_scene_planner import stage_scene_plan  # noqa: E402
    from pipeline.mixed_workflow.stage3_scene_designer import (  # noqa: E402
        generate_scene_design,
        generate_scene_designs_batch,
        stage_scene_designs,
        write_split_scene_design_files,
    )
    from pipeline.mixed_workflow.stage35_layout_designer import stage_scene_layouts  # noqa: E402
    from pipeline.mixed_workflow.stage4_codegen import stage_codegen_video  # noqa: E402
    from pipeline.mixed_workflow.stage5_fixer import stage_fix_code, stage_render_fix_loop  # noqa: E402
else:
    from pipeline.run_layout import RunLayout  # noqa: E402
    from .common import (  # noqa: E402
        RUNS_DIR,
        _slugify,
        _split_analyst_payload,
        _write_text,
        assemble_existing_llm4_fragments,
        build_client,
        load_stage1_analysis,
        load_stage1_drawing_brief,
        load_stage1_problem_solving,
        load_stage35_layouts,
        reset_case_outputs,
    )
    from .stage1_analyst import stage_analyst  # noqa: E402
    from .stage2_scene_planner import stage_scene_plan  # noqa: E402
    from .stage3_scene_designer import (  # noqa: E402
        generate_scene_design,
        generate_scene_designs_batch,
        stage_scene_designs,
        write_split_scene_design_files,
    )
    from .stage35_layout_designer import stage_scene_layouts  # noqa: E402
    from .stage4_codegen import stage_codegen_video  # noqa: E402
    from .stage5_fixer import stage_fix_code, stage_render_fix_loop  # noqa: E402


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Mixed workflow pipeline")
    p.add_argument("-r", "--requirement", type=str, default="")
    p.add_argument("--requirement-file", type=str, default="")
    p.add_argument("--run-dir", type=str, default="")
    p.add_argument("--quality", choices=["l", "m", "h"], default="l", help="manim render quality")
    p.add_argument("--render-timeout-s", type=int, default=300, help="single render timeout in seconds")
    p.add_argument("--max-fix-rounds", type=int, default=5)
    p.add_argument("--max-static-fix-rounds", type=int, default=3, help="deprecated; kept for compatibility")
    p.add_argument("--no-render", action="store_true", help="only generate code; do not render")
    return p.parse_args()


def _read_requirement(args: argparse.Namespace) -> str:
    if args.requirement:
        return args.requirement.strip()
    if args.requirement_file:
        return Path(args.requirement_file).read_text(encoding="utf-8").strip()
    if args.run_dir:
        req_path = Path(args.run_dir) / "requirement.txt"
        if req_path.exists():
            return req_path.read_text(encoding="utf-8").strip()
    raise SystemExit("requirement is empty: provide -r / --requirement-file, or use --run-dir with requirement.txt")


def main() -> int:
    args = parse_args()
    requirement = _read_requirement(args)

    run_id = time.strftime("%Y%m%d_%H%M%S")
    slug = _slugify(requirement)

    inferred: Path | None = None
    if not args.run_dir and args.requirement_file:
        try:
            req_path = Path(args.requirement_file).resolve()
            cases_root = (RUNS_DIR.parent / "cases").resolve()
            rel = req_path.relative_to(cases_root)
            if len(rel.parts) >= 2:
                inferred = cases_root / rel.parts[0]
        except Exception:
            inferred = None

    run_dir = Path(args.run_dir) if args.run_dir else (inferred or (RUNS_DIR / f"{run_id}_{slug}"))
    run_dir.mkdir(parents=True, exist_ok=True)
    layout = RunLayout.from_run_dir(run_dir)
    reset_case_outputs(layout, from_stage=1)

    print(f"[Mixed Workflow] run dir: {run_dir}")
    _write_text(layout.requirement_txt, requirement + "\n")

    client = build_client()

    print("[Mixed Workflow] Stage 1/5: analyst (Claude)")
    _write_text(layout.llm1_system_prompt, client.load_stage_system_prompt("analyst").strip() + "\n")
    analyst = stage_analyst(client, requirement=requirement, out_dir=layout.llm1_dir)
    analysis, problem_solving, drawing_brief = _split_analyst_payload(analyst)

    print("[Mixed Workflow] Stage 2/5: scene planner (Kimi)")
    _write_text(layout.llm2_system_prompt, client.load_stage_system_prompt("scene_planner").strip() + "\n")
    plan = stage_scene_plan(
        client,
        requirement=requirement,
        analysis=analysis,
        problem_solving=problem_solving,
        out_dir=layout.llm2_dir,
    )

    print("[Mixed Workflow] Stage 3/5: scene designer (Kimi)")
    _write_text(layout.llm3_system_prompt, client.load_stage_system_prompt("scene_designer").strip() + "\n")
    scene_designs = stage_scene_designs(
        client,
        requirement=requirement,
        drawing_brief=drawing_brief,
        plan=plan,
        out_dir=layout.llm3_dir,
    )

    print("[Mixed Workflow] Stage 3.5/5: layout designer (Claude)")
    _write_text(layout.llm35_system_prompt, client.load_stage_system_prompt("layout_designer").strip() + "\n")
    scene_layouts = stage_scene_layouts(
        client,
        requirement=requirement,
        drawing_brief=drawing_brief,
        plan=plan,
        scene_designs=scene_designs,
        out_dir=layout.llm35_dir,
    )

    print("[Mixed Workflow] Stage 4/5: codegen (Claude)")
    class_name, code = stage_codegen_video(
        client,
        stage1_problem_solving=problem_solving,
        stage1_drawing_brief=drawing_brief,
        plan=plan,
        scene_designs=scene_designs,
        scene_layouts=scene_layouts,
        out_dir=layout.llm4_dir,
    )

    py_file = layout.llm4_scene_py
    _write_text(py_file, code)
    _write_text(layout.exported_scene_py, code)
    _write_text(
        layout.stage4_meta,
        json.dumps(
            {
                "class_name": class_name,
                "codegen_mode": "batch_llm4",
                "sub_stages": ["framework", "batch_codegen", "assemble"],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    print(f"[Mixed Workflow] generated: {py_file} (class_name={class_name})")

    if args.no_render:
        return 0

    print("[Mixed Workflow] render + fix loop (Claude fixer)")
    class_name, ok, mp4_path, last_err, _last_attempt = stage_render_fix_loop(
        client,
        class_name=class_name,
        py_file=py_file,
        layout=layout,
        quality=args.quality,
        render_timeout_s=int(args.render_timeout_s),
        max_fix_rounds=int(args.max_fix_rounds),
    )
    if ok:
        print(f"[Mixed Workflow] render success -> {mp4_path}")
        return 0

    print("[Mixed Workflow] render failed")
    _write_text(run_dir / "FAILED.txt", f"render failed after {args.max_fix_rounds} rounds\n\n{last_err}")
    return 5


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        raise
