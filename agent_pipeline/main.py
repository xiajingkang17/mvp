"""
Multi-agent Manim generation-evaluation loop.

Flow:
  1. CodeGen agent produces Manim code from a student request.
  2. Renderer invokes Manim. On failure the CodeGen agent keeps repairing the
     code until it reaches the configured retry limit.
  3. The eval pipeline scores the rendered video (CV + VLM).
  4. If the video fails QA, or Round 1 never produces a completed video, the
     CodeGen agent revises the code and Round 2 runs as a rescue pass.
  5. The best scored round is selected, with a rendered-video fallback if QA
     reports are missing.
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import shutil
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

from .asset_resolver import resolve_local_assets
from .code_gen import CodeGenAgent
from .evaluator import collect_keyframes, evaluate
from .renderer import RenderResult, render_scene
from .teaching_planner import TeachingPlannerAgent
from .tts import generate_narration, has_audio_stream, merge_audio_video

# =====================================================================
# Configuration constants (override via .env or process env)
# =====================================================================

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

API_KEY = os.environ.get("OPENAI_API_KEY", "")
BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o")
MANIM_QUALITY = os.environ.get("MANIM_QUALITY", "-qh --fps 60")
RUNS_DIR = ROOT_DIR / "runs"
USE_LOCAL_ICONS = os.environ.get("A4L_USE_LOCAL_ICONS", "1").lower() not in {
    "0",
    "false",
    "no",
}


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, str(default)))
    except ValueError:
        return default


SYNTAX_FIX_MAX_ATTEMPTS = max(1, _int_env("A4L_SYNTAX_FIX_MAX_ATTEMPTS", 4))
RENDER_FIX_MAX_ATTEMPTS = max(1, _int_env("A4L_RENDER_FIX_MAX_ATTEMPTS", 4))
MANIM_TIMEOUT_SEC = max(300, _int_env("MANIM_TIMEOUT_SEC", 1200))

# =====================================================================
# Helpers
# =====================================================================


def _log(msg: str) -> None:
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")


def _detect_chinese_in_mathtex(code: str) -> str:
    """Scan code for Chinese chars inside MathTex/Tex and return a warning."""
    import re

    issues = []
    for match in re.finditer(r"(MathTex|Tex)\s*\(", code):
        start = match.end()
        depth = 1
        i = start
        while i < len(code) and depth > 0:
            if code[i] == "(":
                depth += 1
            elif code[i] == ")":
                depth -= 1
            i += 1
        fragment = code[start:i]
        chinese = re.findall(r"[\u4e00-\u9fff]+", fragment)
        if chinese:
            issues.append(
                f"  Found Chinese '{','.join(chinese)}' inside "
                f"{match.group(1)}() near: ...{fragment[:80]}..."
            )
    if issues:
        return "\n\nAUTO-DETECTED ISSUES (fix these first!):\n" + "\n".join(issues)
    return ""


def _check_python_syntax(code: str) -> Optional[str]:
    """Return a readable syntax error string, or None if code parses."""
    try:
        ast.parse(code)
        return None
    except SyntaxError as exc:
        line = ""
        lines = code.splitlines()
        if exc.lineno and 1 <= exc.lineno <= len(lines):
            line = lines[exc.lineno - 1]
        pointer = ""
        if exc.offset and line:
            pointer = " " * max(exc.offset - 1, 0) + "^"
        return (
            f"{exc.__class__.__name__}: {exc.msg}\n"
            f"line {exc.lineno}, column {exc.offset}\n"
            f"{line}\n{pointer}"
        )


def _repair_syntax_before_render(
    agent: CodeGenAgent,
    code: str,
    round_dir: Path,
    label: str,
    max_attempts: int = SYNTAX_FIX_MAX_ATTEMPTS,
) -> tuple[str, Optional[str]]:
    """Fix Python syntax errors before calling Manim."""
    syntax_error = _check_python_syntax(code)
    attempt = 0
    while syntax_error and attempt < max_attempts:
        attempt += 1
        _log(f"{label}: Python syntax invalid before render - asking LLM to fix (attempt {attempt}) ...")
        extra_hint = (
            "\n\nThis is a Python syntax failure, not a Manim layout issue.\n"
            "Fix the code so it parses first. Pay special attention to:\n"
            "- unterminated string literals\n"
            "- broken multiline Chinese strings\n"
            "- missing closing brackets or parentheses\n"
            "- truncated code near the end of the file\n"
            "- leaving every `self.speak(...)` / `self.speak_with_subtitle(...)` string on one logical Python string literal\n"
        )
        code = agent.fix(code, syntax_error + extra_hint)
        (round_dir / f"scene_syntax_fixed_{attempt}.py").write_text(code, encoding="utf-8")
        syntax_error = _check_python_syntax(code)
    return code, syntax_error


def _try_render(
    agent: CodeGenAgent,
    code: str,
    round_dir: Path,
    label: str,
) -> tuple[str, RenderResult]:
    """Render *code*; on failure keep repairing until retry budget is exhausted."""
    result = RenderResult(success=False, error_log="", scene_name="")

    for attempt in range(RENDER_FIX_MAX_ATTEMPTS + 1):
        code, syntax_error = _repair_syntax_before_render(agent, code, round_dir, label)
        if syntax_error:
            _log(f"{label}: syntax fix failed before render")
            result = RenderResult(success=False, error_log=syntax_error, scene_name="")
        else:
            render_msg = f"{label}: rendering"
            if attempt:
                render_msg += f" after fix {attempt}"
            _log(render_msg + " ...")
            result = render_scene(
                code,
                round_dir,
                quality_flags=MANIM_QUALITY,
                timeout_sec=MANIM_TIMEOUT_SEC,
            )
            if result.success:
                if attempt:
                    _log(f"{label}: fix {attempt} succeeded, render OK")
                else:
                    _log(f"{label}: render OK")
                return code, result

        if attempt >= RENDER_FIX_MAX_ATTEMPTS:
            _log(f"{label}: render still failed after {attempt} fix attempt(s)")
            break

        _log(
            f"{label}: render FAILED - asking LLM to fix "
            f"(attempt {attempt + 1}/{RENDER_FIX_MAX_ATTEMPTS}) ..."
        )
        error_info = result.error_log + _detect_chinese_in_mathtex(code)
        code = agent.fix(code, error_info)
        (round_dir / f"scene_fixed_{attempt + 1}.py").write_text(code, encoding="utf-8")

    return code, result


def _try_eval(
    video_path: Path,
    eval_dir: Path,
    label: str,
) -> Optional[Dict]:
    """Run the eval pipeline. Returns the report dict or None on error."""
    _log(f"{label}: evaluating video ...")
    try:
        report = evaluate(
            video_path,
            eval_dir,
            api_key=API_KEY,
            base_url=BASE_URL,
            model=MODEL,
        )
        score = report.get("overall_score", 0)
        passed = report.get("overall_passed", False)
        status = "PASS" if passed else "FAIL"
        _log(f"{label}: score={score:.2f} [{status}]")
        return report
    except Exception as exc:
        _log(f"{label}: evaluation error - {exc}")
        return None


def _round_info(n: int, render: RenderResult, report: Optional[Dict]) -> Dict:
    info = {
        "round": n,
        "render_success": render.success,
        "video": str(render.video_path) if render.video_path else None,
        "eval_score": report.get("overall_score") if report else None,
        "eval_passed": report.get("overall_passed") if report else None,
    }
    if render.error_log:
        info["render_warning" if render.success else "render_error"] = render.error_log[-1500:]
    return info


def _find_keyframes(eval_dir: Path) -> List[Path]:
    """Collect keyframe images from an eval output dir."""
    keyframes = collect_keyframes(eval_dir)
    if keyframes:
        return keyframes
    for sub in eval_dir.rglob("*.jpg"):
        keyframes.append(sub)
    return sorted(keyframes)


# =====================================================================
# Main pipeline
# =====================================================================


def run_pipeline(
    request_text: str,
    image_path: Optional[Path] = None,
    run_dir: Optional[Path] = None,
) -> Dict:
    """Execute the full generate-render-evaluate-improve loop."""
    if run_dir is None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_dir = RUNS_DIR / ts
    run_dir.mkdir(parents=True, exist_ok=True)

    (run_dir / "request.txt").write_text(request_text, encoding="utf-8")
    if image_path and image_path.exists():
        shutil.copy2(str(image_path), str(run_dir / f"request_image{image_path.suffix}"))

    _log("Teaching planner: building lesson structure ...")
    planner = TeachingPlannerAgent(api_key=API_KEY, base_url=BASE_URL, model=MODEL)
    agent = CodeGenAgent(api_key=API_KEY, base_url=BASE_URL, model=MODEL)
    teaching_plan: Dict[str, Any] = planner.plan(request_text, image_path)
    _log(f"Teaching planner: {len(teaching_plan.get('sections', []))} section(s) ready")

    assets_info: Dict[str, Any] = {
        "enabled": USE_LOCAL_ICONS,
        "icon_dir": str((ROOT_DIR / "icon").resolve()),
        "available_icon_count": 0,
        "selected_assets": [],
    }
    if USE_LOCAL_ICONS:
        _log("Asset resolver: selecting local icons ...")
        try:
            assets_info = resolve_local_assets(
                request_text,
                teaching_plan,
                api_key=API_KEY,
                base_url=BASE_URL,
                model=MODEL,
            )
            selected_assets = assets_info.get("selected_assets", [])
            teaching_plan["selected_assets"] = selected_assets
            _log(f"Asset resolver: selected {len(selected_assets)} icon(s)")
        except Exception as exc:
            teaching_plan["selected_assets"] = []
            _log(f"Asset resolver: skipped due to error - {exc}")
    else:
        teaching_plan["selected_assets"] = []

    selected_assets_path = run_dir / "selected_assets.json"
    selected_assets_path.write_text(
        json.dumps(assets_info, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    teaching_plan_path = run_dir / "teaching_plan.json"
    teaching_plan_path.write_text(
        json.dumps(teaching_plan, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    summary: Dict[str, Any] = {
        "request": request_text,
        "image": str(image_path) if image_path else None,
        "teaching_plan_file": str(teaching_plan_path),
        "selected_assets_file": str(selected_assets_path),
        "selected_assets_count": len(teaching_plan.get("selected_assets", [])),
        "rounds": [],
        "final_video": None,
        "final_score": None,
        "final_passed": None,
    }

    candidates: list[tuple[float, str, int]] = []
    rendered_candidates: list[tuple[int, str]] = []

    # ==================================================================
    # Round 1
    # ==================================================================
    _log("Round 1: generating Manim code ...")
    code = agent.generate(request_text, image_path, teaching_plan=teaching_plan)

    r1_dir = run_dir / "round1"
    code, r1_render = _try_render(agent, code, r1_dir, "Round 1")

    r1_report: Optional[Dict] = None
    r1_eval_dir = r1_dir / "eval"
    if r1_render.success and r1_render.video_path:
        rendered_candidates.append((1, str(r1_render.video_path)))
        r1_report = _try_eval(r1_render.video_path, r1_eval_dir, "Round 1")

    summary["rounds"].append(_round_info(1, r1_render, r1_report))
    if r1_report and r1_render.video_path:
        candidates.append((r1_report.get("overall_score", 0), str(r1_render.video_path), 1))

    if r1_report and r1_report.get("overall_passed"):
        _log("Round 1 PASSED - done!")
        summary["final_video"] = str(r1_render.video_path)
        summary["final_score"] = r1_report["overall_score"]
        summary["final_passed"] = True
        _add_tts(agent, code, request_text, run_dir, summary)
        _save_summary(run_dir, summary)
        return summary

    # ==================================================================
    # Round 2
    # ==================================================================
    if not r1_render.success:
        _log("Round 2: Round 1 did not produce a video - running a render-rescue pass ...")
        rescue_hint = r1_render.error_log or "Round 1 did not produce a completed video."
        code = agent.fix(code, rescue_hint)
    else:
        _log("Round 2: improving code with evaluation feedback + keyframe screenshots ...")
        keyframes = _find_keyframes(r1_eval_dir)
        if keyframes:
            _log(f"  Sending {len(keyframes)} keyframe(s) to LLM for visual feedback")
        feedback = r1_report or {"issues": [], "dimensions": [], "overall_score": 0}
        code = agent.improve(
            code,
            feedback,
            keyframe_paths=keyframes or None,
            teaching_plan=teaching_plan,
        )

    r2_dir = run_dir / "round2"
    code, r2_render = _try_render(agent, code, r2_dir, "Round 2")

    r2_report: Optional[Dict] = None
    r2_eval_dir = r2_dir / "eval"
    if r2_render.success and r2_render.video_path:
        rendered_candidates.append((2, str(r2_render.video_path)))
        r2_report = _try_eval(r2_render.video_path, r2_eval_dir, "Round 2")

    summary["rounds"].append(_round_info(2, r2_render, r2_report))
    if r2_report and r2_render.video_path:
        candidates.append((r2_report.get("overall_score", 0), str(r2_render.video_path), 2))

    # ==================================================================
    # Pick the best round
    # ==================================================================
    if candidates:
        candidates.sort(key=lambda item: item[0], reverse=True)
        best_score, best_video, best_round = candidates[0]
        summary["final_video"] = best_video
        summary["final_score"] = best_score
        summary["final_passed"] = any(item[0] >= 0.65 for item in candidates)
        _log(f"Best result: Round {best_round} (score={best_score:.2f})")
    elif rendered_candidates:
        rendered_candidates.sort(key=lambda item: item[0], reverse=True)
        best_round, best_video = rendered_candidates[0]
        summary["final_video"] = best_video
        summary["final_score"] = None
        summary["final_passed"] = False
        _log(f"Best available render: Round {best_round} (no eval score available)")
    else:
        summary["final_passed"] = False

    _add_tts(agent, code, request_text, run_dir, summary)
    _log(f"Done - final score: {summary['final_score']}, passed: {summary['final_passed']}")
    _save_summary(run_dir, summary)
    return summary


def _add_tts(
    agent: CodeGenAgent,
    code: str,
    request_text: str,
    run_dir: Path,
    summary: Dict[str, Any],
) -> None:
    """Generate fallback narration and merge it when the final video is silent."""
    if not summary.get("final_video"):
        return

    video_path = Path(summary["final_video"])
    if not video_path.exists():
        return

    if has_audio_stream(video_path):
        _log("Final render already contains audio track - skipping fallback narration merge")
        return

    _log("Final render is silent - generating fallback narration with TTS ...")
    try:
        script = agent.narrate(code, request_text)
        if not script:
            _log("  Narration script empty - skipping TTS")
            return
        _log(f"  Narration script: {len(script)} paragraphs")

        audio_path = generate_narration(script, run_dir)
        if not audio_path:
            _log("  TTS audio generation failed")
            return
        _log(f"  Audio generated: {audio_path}")

        video_with_audio = run_dir / "final_with_audio.mp4"
        ok = merge_audio_video(video_path, audio_path, video_with_audio)
        if ok:
            summary["final_video_with_audio"] = str(video_with_audio)
            _log(f"  Video+audio merged: {video_with_audio}")
        else:
            _log("  Audio merge failed - delivering silent video")
    except Exception as exc:
        _log(f"  TTS error: {exc} - delivering silent video")


def _save_summary(run_dir: Path, summary: Dict[str, Any]) -> None:
    path = run_dir / "summary.json"
    path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    _log(f"Summary saved: {path}")


# =====================================================================
# CLI
# =====================================================================


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="agent_pipeline",
        description="Multi-agent Manim generation-evaluation loop",
    )
    parser.add_argument("request", nargs="?", default=None, help="Student request text")
    parser.add_argument("--image", type=Path, default=None, help="Optional input image")
    parser.add_argument("--run-dir", type=Path, default=None, help="Custom output directory")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if not API_KEY:
        print("Error: OPENAI_API_KEY is not set. Put it in .env or export it in the shell and try again.")
        return 1

    if args.request is None and args.image is None:
        print('Usage: python -m agent_pipeline "request text" [--image img.png]')
        return 1

    request_text = args.request or "Generate an animation lesson from the image."

    t0 = time.time()
    summary = run_pipeline(request_text, args.image, args.run_dir)
    elapsed = time.time() - t0

    print(f"\n{'=' * 60}")
    print(f"  Pipeline finished in {elapsed:.0f}s")
    print(f"  Rounds: {len(summary['rounds'])}")
    for round_info in summary["rounds"]:
        round_number = round_info["round"]
        score = round_info.get("eval_score")
        passed = round_info.get("eval_passed")
        rendered = "YES" if round_info.get("render_success") else "NO"
        print(f"    Round {round_number}: render={rendered}, score={score}, passed={passed}")
    print(f"  Final video:  {summary['final_video']}")
    audio_video = summary.get("final_video_with_audio")
    if audio_video:
        print(f"  With audio:   {audio_video}")
    print(f"  Final score:  {summary['final_score']}")
    print(f"  Final passed: {summary['final_passed']}")
    print(f"{'=' * 60}")

    return 0 if summary.get("final_video") else 1
