from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    REPO_ROOT = Path(__file__).resolve().parents[3]
    repo_text = str(REPO_ROOT)
    if repo_text not in sys.path:
        sys.path.insert(0, repo_text)

from Manim4Teach.pipeline.core.env import load_dotenv  # noqa: E402
from Manim4Teach.pipeline.core.question_parser import parse_requirement_inputs  # noqa: E402
from Manim4Teach.pipeline.stage2.client import build_stage2_client  # noqa: E402
from Manim4Teach.pipeline.stage2.io_utils import ensure_dir, now_stamp, read_json, slugify, write_json  # noqa: E402
from Manim4Teach.pipeline.stage2.llm_scene import DEFAULT_SCENE_CLASS, generate_first_draft, revise_scene_code  # noqa: E402
from Manim4Teach.pipeline.stage2.preview_render import run_preview_render  # noqa: E402
from Manim4Teach.pipeline.stage2.review_rules import run_rule_review  # noqa: E402
from Manim4Teach.pipeline.stage2.review_vlm import run_vlm_review  # noqa: E402
from Manim4Teach.pipeline.stage2.runtime_fix import run_runtime_fix_loop  # noqa: E402
from Manim4Teach.pipeline.stage2.static_checks import run_static_checks  # noqa: E402


def _load_env_file() -> Path:
    env_path = Path(__file__).resolve().parents[2] / ".env"
    if not env_path.exists():
        raise FileNotFoundError(f"缺少 .env 文件: {env_path}")
    if not load_dotenv(path=env_path):
        raise RuntimeError(f".env 加载失败: {env_path}")
    return env_path


def _read_requirement(args: argparse.Namespace) -> str:
    try:
        requirement, _images = parse_requirement_inputs(
            requirement=str(args.requirement or ""),
            requirement_file=str(args.requirement_file or ""),
        )
        return requirement or "请根据 analysis_packet 生成一版可看教学视频。"
    except ValueError:
        return "请根据 analysis_packet 生成一版可看教学视频。"


def _default_out_dir(requirement: str) -> Path:
    run_root = Path(__file__).resolve().parents[2] / "runs"
    return run_root / f"{now_stamp()}_{slugify(requirement)}" / "llm2"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Manim4Teach LLM2 Director Loop")
    parser.add_argument("--analysis-packet", type=str, required=True, help="stage1_analysis_packet.json 路径")
    parser.add_argument("--requirement", type=str, default="")
    parser.add_argument("--requirement-file", type=str, default="")
    parser.add_argument("--provider", choices=["claude", "anthropic"], default="claude")
    parser.add_argument("--max-rounds", type=int, default=3, help="建议 2-4 轮")
    parser.add_argument("--out-dir", type=str, default="")
    parser.add_argument("--scene-class", type=str, default=DEFAULT_SCENE_CLASS)
    parser.add_argument("--skip-preview", action="store_true")
    parser.add_argument(
        "--clean-out-dir",
        dest="clean_out_dir",
        action="store_true",
        default=True,
        help="运行前清空 out-dir（默认开启）",
    )
    parser.add_argument(
        "--no-clean-out-dir",
        dest="clean_out_dir",
        action="store_false",
        help="不清空 out-dir，保留历史文件",
    )
    return parser.parse_args()


def _cleanup_minimal_outputs(out_dir: Path, final_dir: Path) -> None:
    keep_final_names = {"scene.py", "vlm_review.json", "runtime_fix.json", "preview.mp4", "meta.json"}

    # 清理 final 目录中非最小产物文件
    for child in list(final_dir.iterdir()):
        if child.name in keep_final_names:
            continue
        if child.is_dir():
            shutil.rmtree(child, ignore_errors=True)
        else:
            child.unlink(missing_ok=True)

    # 清理 out_dir 下除 final 外的所有文件/目录
    for child in list(out_dir.iterdir()):
        if child.name == "final":
            continue
        if child.is_dir():
            shutil.rmtree(child, ignore_errors=True)
        else:
            child.unlink(missing_ok=True)


def main() -> int:
    args = parse_args()
    env_path = _load_env_file()
    provider = "anthropic" if args.provider == "claude" else args.provider
    max_rounds = max(1, min(int(args.max_rounds), 6))

    analysis_packet_path = Path(args.analysis_packet).resolve()
    if not analysis_packet_path.exists():
        raise FileNotFoundError(f"analysis_packet 不存在: {analysis_packet_path}")
    analysis_packet = read_json(analysis_packet_path)
    requirement = _read_requirement(args)
    out_dir = Path(args.out_dir).resolve() if args.out_dir else _default_out_dir(requirement)
    if bool(args.clean_out_dir) and out_dir.exists():
        shutil.rmtree(out_dir, ignore_errors=True)
    ensure_dir(out_dir)

    client = build_stage2_client(provider=provider)  # type: ignore[arg-type]
    scene_class = str(args.scene_class or DEFAULT_SCENE_CLASS).strip() or DEFAULT_SCENE_CLASS

    prev_scene_code = ""
    prev_rule_issues: list[dict[str, Any]] = []
    prev_vlm_issues: list[dict[str, Any]] = []
    final_round = 0
    stop_reason = "max_rounds_reached"
    final_scene_path: Path | None = None
    final_vlm_report: dict[str, Any] | None = None
    final_preview_video_path: Path | None = None
    final_rule_report: dict[str, Any] | None = None
    final_static_report: dict[str, Any] | None = None
    final_runtime_fix_report: dict[str, Any] | None = None
    final_preview_ok = False
    final_class_name = scene_class

    for round_index in range(1, max_rounds + 1):
        final_round = round_index
        round_dir = ensure_dir(out_dir / f"round_{round_index:02d}")
        if round_index == 1:
            class_name, scene_path = generate_first_draft(
                client=client,
                requirement=requirement,
                analysis_packet=analysis_packet,
                out_dir=round_dir,
                scene_class=scene_class,
            )
        else:
            class_name, scene_path = revise_scene_code(
                client=client,
                requirement=requirement,
                analysis_packet=analysis_packet,
                current_code=prev_scene_code,
                rule_issues=prev_rule_issues,
                vlm_issues=prev_vlm_issues,
                out_dir=round_dir,
                scene_class=scene_class,
            )

        final_class_name = class_name
        current_code = scene_path.read_text(encoding="utf-8")
        static_report = run_static_checks(scene_path, out_path=None)
        final_static_report = static_report

        preview_report = None
        if not args.skip_preview:
            preview_report = run_preview_render(
                scene_path=scene_path,
                class_name=class_name,
                out_dir=round_dir / "preview",
                round_index=round_index,
                write_report_path=None,
            )
            video_text = str((preview_report.get("artifacts") or {}).get("video") or "")
            if video_text:
                maybe_video = Path(video_text)
                if maybe_video.exists():
                    final_preview_video_path = maybe_video
            final_preview_ok = bool(preview_report.get("ok"))

            if (not static_report.get("compile_ok", False)) or (preview_report is not None and not preview_report.get("ok")):
                runtime_fix_report = run_runtime_fix_loop(
                    client=client,
                    requirement=requirement,
                    analysis_packet=analysis_packet,
                    scene_path=scene_path,
                    class_name=class_name,
                    static_report=static_report,
                    preview_report=preview_report,
                    out_dir=round_dir / "runtime_fix",
                    round_index=round_index,
                    max_attempts=2,
                    scene_class=scene_class,
                    write_report_path=round_dir / "runtime_fix_report.json",
                )
                final_runtime_fix_report = runtime_fix_report
                runtime_scene_path = Path(str(runtime_fix_report.get("scene_path") or scene_path))
                if runtime_scene_path.exists():
                    scene_path = runtime_scene_path
                    class_name = str(runtime_fix_report.get("class_name") or class_name)
                    current_code = scene_path.read_text(encoding="utf-8")
                static_report = dict(runtime_fix_report.get("static_report") or static_report)
                preview_report = dict(runtime_fix_report.get("preview_report") or preview_report or {})
                final_static_report = static_report
                video_text = str((preview_report.get("artifacts") or {}).get("video") or "")
                if video_text:
                    maybe_video = Path(video_text)
                    if maybe_video.exists():
                        final_preview_video_path = maybe_video
                final_preview_ok = bool(preview_report.get("ok"))

        rule_report = run_rule_review(
            static_report=static_report,
            preview_report=preview_report,
            preview_required=not args.skip_preview,
            out_path=None,
        )
        final_rule_report = rule_report
        vlm_report = run_vlm_review(
            preview_report=preview_report,
            requirement=requirement,
            analysis_packet=analysis_packet,
            out_path=None,
        )
        final_vlm_report = vlm_report

        vlm_should_revise = bool(vlm_report.get("should_revise", False))
        combined_should_revise = bool(rule_report.get("should_revise")) or vlm_should_revise

        final_scene_path = scene_path
        prev_scene_code = current_code
        prev_rule_issues = list(rule_report.get("top_issues") or [])
        prev_vlm_issues = list(vlm_report.get("top_issues") or vlm_report.get("issues") or [])

        if not combined_should_revise:
            stop_reason = "quality_gate_passed"
            break

    final_dir = ensure_dir(out_dir / "final")
    if final_scene_path is not None and final_scene_path.exists():
        shutil.copy2(final_scene_path, final_dir / "scene.py")
    if final_vlm_report is not None:
        write_json(final_dir / "vlm_review.json", final_vlm_report)
    if final_runtime_fix_report is not None:
        write_json(final_dir / "runtime_fix.json", final_runtime_fix_report)
    if final_preview_video_path is not None and final_preview_video_path.exists():
        shutil.copy2(final_preview_video_path, final_dir / "preview.mp4")

    meta = {
        "provider": provider,
        "analysis_packet_path": str(analysis_packet_path),
        "requirement_preview": (requirement[:200] + "...") if len(requirement) > 200 else requirement,
        "scene_class": final_class_name,
        "final_round": final_round,
        "stop_reason": stop_reason,
        "preview_enabled": not args.skip_preview,
        "preview_ok": final_preview_ok,
        "final_scene": str(final_dir / "scene.py"),
        "final_preview_video": str(final_dir / "preview.mp4") if (final_dir / "preview.mp4").exists() else "",
        "rule_review": {
            "max_severity": str((final_rule_report or {}).get("max_severity", "low")),
            "issue_count": int((final_rule_report or {}).get("issue_count", 0)),
            "top_issues": list((final_rule_report or {}).get("top_issues") or []),
            "should_revise": bool((final_rule_report or {}).get("should_revise", False)),
        },
        "vlm_review": {
            "enabled": bool((final_vlm_report or {}).get("enabled", False)),
            "status": str((final_vlm_report or {}).get("status", "")),
            "max_severity": str((final_vlm_report or {}).get("max_severity", "low")),
            "issue_count": int((final_vlm_report or {}).get("issue_count", 0)),
            "top_issues": list((final_vlm_report or {}).get("top_issues") or []),
            "should_revise": bool((final_vlm_report or {}).get("should_revise", False)),
        },
        "static_check": {
            "compile_ok": bool((final_static_report or {}).get("compile_ok", False)),
            "undefined_name_candidates": list((final_static_report or {}).get("undefined_name_candidates") or []),
            "heuristic_flags": dict((final_static_report or {}).get("heuristic_flags") or {}),
        },
        "runtime_fix": {
            "status": str((final_runtime_fix_report or {}).get("status", "not_needed")),
            "fixed": bool((final_runtime_fix_report or {}).get("fixed", False)),
            "attempt_count": int((final_runtime_fix_report or {}).get("attempt_count", 0)),
        },
        "env_path": str(env_path),
    }
    write_json(final_dir / "meta.json", meta)

    _cleanup_minimal_outputs(out_dir, final_dir)

    print(f"[Manim4Teach][LLM2] provider: {provider}")
    print(f"[Manim4Teach][LLM2] rounds: {final_round}")
    print(f"[Manim4Teach][LLM2] stop_reason: {stop_reason}")
    print(f"[Manim4Teach][LLM2] output: {final_dir / 'scene.py'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
