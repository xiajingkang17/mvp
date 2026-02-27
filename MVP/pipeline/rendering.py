from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Literal


Quality = Literal["l", "m", "h"]


_SCENE_CLASS_RE = re.compile(r"class\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(([^)]*Scene[^)]*)\)\s*:")


@dataclass(frozen=True)
class RenderResult:
    ok: bool
    mp4_path: Path | None
    stdout: str
    stderr: str
    returncode: int


def detect_scene_classes(code: str) -> list[str]:
    return [m.group(1) for m in _SCENE_CLASS_RE.finditer(code)]


def render_scene(
    *,
    py_file: Path,
    class_name: str,
    media_dir: Path,
    quality: Quality = "l",
    timeout_s: int = 300,
) -> RenderResult:
    """
    调用 manim 渲染单个 Scene。返回 stderr 以便进入修复循环。
    """

    media_dir.mkdir(parents=True, exist_ok=True)
    output_file = f"{class_name}.mp4"

    cmd = [
        "manim",
        f"-q{quality}",
        str(py_file),
        class_name,
        "--media_dir",
        str(media_dir),
        "--output_file",
        output_file,
    ]

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_s)
    except subprocess.TimeoutExpired as exc:
        return RenderResult(
            ok=False,
            mp4_path=None,
            stdout=exc.stdout or "",
            stderr=(exc.stderr or "") + f"\n[timeout] 渲染超时：{timeout_s}s",
            returncode=124,
        )
    except FileNotFoundError as exc:
        return RenderResult(
            ok=False,
            mp4_path=None,
            stdout="",
            stderr=f"[error] 找不到 manim 命令：{exc}. 请确认已安装 Manim 且已加入 PATH。",
            returncode=127,
        )

    mp4 = None
    if proc.returncode == 0:
        hits = list(media_dir.rglob(output_file))
        if hits:
            # 同名文件通常唯一；取最新的
            mp4 = max(hits, key=lambda p: p.stat().st_mtime)

    return RenderResult(
        ok=proc.returncode == 0 and mp4 is not None,
        mp4_path=mp4,
        stdout=proc.stdout or "",
        stderr=proc.stderr or "",
        returncode=int(proc.returncode),
    )


def concat_videos_ffmpeg(*, mp4_list: list[Path], output_mp4: Path) -> None:
    """
    用 ffmpeg concat 拼接成片。若系统没有 ffmpeg，会报错。
    """

    if not mp4_list:
        raise ValueError("mp4_list 为空，无法合并")

    output_mp4.parent.mkdir(parents=True, exist_ok=True)
    list_file = output_mp4.with_suffix(".txt")
    lines = [f"file '{p.as_posix()}'" for p in mp4_list]
    list_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(list_file),
        "-c",
        "copy",
        str(output_mp4),
    ]
    subprocess.run(cmd, check=True, capture_output=True, text=True)
