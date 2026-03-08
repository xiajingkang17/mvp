from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any

from .io_utils import ensure_dir, write_json


def _run_command(args: list[str], *, cwd: Path | None = None) -> dict[str, Any]:
    proc = subprocess.run(
        args,
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return {
        "args": args,
        "returncode": int(proc.returncode),
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }


def _find_latest_mp4(root: Path) -> Path | None:
    files = sorted(root.rglob("*.mp4"), key=lambda p: p.stat().st_mtime)
    return files[-1] if files else None


def _probe_duration_seconds(video_path: Path) -> float:
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        return 6.0
    res = _run_command(
        [
            ffprobe,
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(video_path),
        ]
    )
    if res["returncode"] != 0:
        return 6.0
    try:
        return max(1.0, float(str(res["stdout"]).strip()))
    except ValueError:
        return 6.0


def _extract_keyframes(video_path: Path, out_dir: Path, *, duration: float) -> list[str]:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        return []
    ensure_dir(out_dir)
    frame_paths: list[str] = []
    for idx, frac in enumerate((0.15, 0.5, 0.85), start=1):
        ts = max(0.0, min(duration - 0.1, duration * frac))
        out_path = out_dir / f"keyframe_{idx:02d}.jpg"
        res = _run_command(
            [
                ffmpeg,
                "-y",
                "-ss",
                f"{ts:.2f}",
                "-i",
                str(video_path),
                "-frames:v",
                "1",
                str(out_path),
            ]
        )
        if res["returncode"] == 0 and out_path.exists():
            frame_paths.append(str(out_path))
    return frame_paths


def _extract_core_clips(video_path: Path, out_dir: Path, *, duration: float) -> list[str]:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        return []
    ensure_dir(out_dir)
    clips: list[str] = []
    segments = [(0.25, 0.18), (0.62, 0.18)]
    for idx, (center_frac, width_frac) in enumerate(segments, start=1):
        seg_dur = max(1.8, duration * width_frac)
        start = max(0.0, duration * center_frac - seg_dur / 2.0)
        if start + seg_dur > duration:
            seg_dur = max(0.8, duration - start)
        out_path = out_dir / f"clip_{idx:02d}.mp4"
        res = _run_command(
            [
                ffmpeg,
                "-y",
                "-ss",
                f"{start:.2f}",
                "-i",
                str(video_path),
                "-t",
                f"{seg_dur:.2f}",
                "-c:v",
                "libx264",
                "-preset",
                "veryfast",
                "-crf",
                "28",
                "-c:a",
                "aac",
                "-b:a",
                "96k",
                str(out_path),
            ]
        )
        if res["returncode"] == 0 and out_path.exists():
            clips.append(str(out_path))
    return clips


def run_preview_render(
    *,
    scene_path: Path,
    class_name: str,
    out_dir: Path,
    round_index: int,
    write_report_path: Path | None = None,
) -> dict[str, Any]:
    ensure_dir(out_dir)
    media_dir = ensure_dir(out_dir / "manim_media")
    keyframe_dir = out_dir / "keyframes"
    clip_dir = out_dir / "clips"

    render_cmd = [
        "python",
        "-m",
        "manim",
        "-ql",
        str(scene_path),
        class_name,
        "--media_dir",
        str(media_dir),
        "-o",
        f"preview_round_{int(round_index):02d}",
    ]
    render_res = _run_command(render_cmd, cwd=scene_path.parent)
    video_path = _find_latest_mp4(media_dir) if render_res["returncode"] == 0 else None

    keyframes: list[str] = []
    clips: list[str] = []
    duration = 0.0
    if video_path is not None and video_path.exists():
        duration = _probe_duration_seconds(video_path)
        keyframes = _extract_keyframes(video_path, keyframe_dir, duration=duration)
        clips = _extract_core_clips(video_path, clip_dir, duration=duration)

    report = {
        "ok": render_res["returncode"] == 0 and video_path is not None,
        "round_index": int(round_index),
        "scene_path": str(scene_path),
        "class_name": class_name,
        "render": {
            "returncode": render_res["returncode"],
            "cmd": render_cmd,
            "stdout_tail": str(render_res["stdout"])[-5000:],
            "stderr_tail": str(render_res["stderr"])[-5000:],
        },
        "artifacts": {
            "video": str(video_path) if video_path else "",
            "duration_seconds": duration,
            "keyframes": keyframes,
            "clips": clips,
        },
    }
    if write_report_path is not None:
        write_json(write_report_path, report)
    return report

