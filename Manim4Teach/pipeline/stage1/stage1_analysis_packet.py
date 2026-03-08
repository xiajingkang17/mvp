from __future__ import annotations

import base64
from pathlib import Path
from typing import Any

from .analysis_packet import normalize_analysis_packet, save_analysis_packet
from ..core.llm_client import LLMClient


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _guess_media_type(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".jpg", ".jpeg"}:
        return "image/jpeg"
    if suffix == ".png":
        return "image/png"
    if suffix == ".webp":
        return "image/webp"
    return "image/jpeg"


def _to_image_block(path: Path) -> dict[str, Any]:
    return {
        "type": "image",
        "source": {
            "type": "base64",
            "media_type": _guess_media_type(path),
            "data": base64.b64encode(path.read_bytes()).decode("ascii"),
        },
    }


def stage_analysis_packet(
    client: LLMClient,
    *,
    requirement: str,
    image_paths: list[Path] | None = None,
    out_dir: Path,
) -> dict[str, Any]:
    user = str(requirement or "").strip()
    images = [Path(p).resolve() for p in (image_paths or [])]
    if not user and not images:
        raise ValueError("requirement 不能为空")

    system = client.load_stage_system_prompt("analysis_packet")
    user_blocks: list[dict[str, Any]] | None = None
    if images:
        if not user:
            user = "请根据附图提取题意并输出 analysis_packet。"
        user_blocks = [{"type": "text", "text": user}]
        user_blocks.extend(_to_image_block(path) for path in images)

    data, raw = client.generate_json(
        stage_key="analysis_packet",
        system_prompt=system,
        user_prompt=user,
        user_blocks=user_blocks,
    )

    packet = normalize_analysis_packet(data)
    out_dir.mkdir(parents=True, exist_ok=True)
    _write_text(out_dir / "stage1_analysis_packet_raw.txt", raw)
    _write_text(out_dir / "stage1_system_prompt.md", system.strip() + "\n")
    save_analysis_packet(out_dir / "stage1_analysis_packet.json", packet)
    return packet
