from __future__ import annotations

import os
import re
from pathlib import Path


_MD_IMAGE_RE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
_LINE_IMAGE_RE = re.compile(r"^\s*(?:image|img|图片|图)\s*[:：]\s*(.+?)\s*$", re.IGNORECASE)


def _normalize_path_token(token: str) -> str:
    text = str(token or "").strip().strip("'\"")
    if text.lower().startswith("file://"):
        text = text[7:].lstrip("/")
    return text.strip()


def _resolve_image_path(token: str, *, base_dir: Path) -> Path:
    normalized = _normalize_path_token(token)
    if not normalized:
        raise ValueError("图片路径不能为空")
    if normalized.lower().startswith(("http://", "https://")):
        raise ValueError(f"question.txt 暂不支持网络图片 URL: {normalized}")
    path = Path(normalized)
    if not path.is_absolute():
        path = (base_dir / path).resolve()
    else:
        path = path.resolve()
    if not path.exists():
        raise FileNotFoundError(f"图片不存在: {path}")
    return path


def parse_question_text(raw_text: str, *, base_dir: Path) -> tuple[str, list[Path]]:
    image_tokens: list[str] = []
    kept_lines: list[str] = []

    for raw_line in str(raw_text or "").splitlines():
        line = raw_line

        line_match = _LINE_IMAGE_RE.match(line)
        if line_match:
            image_tokens.append(line_match.group(1))
            continue

        md_tokens = _MD_IMAGE_RE.findall(line)
        if md_tokens:
            image_tokens.extend(md_tokens)
            line = _MD_IMAGE_RE.sub("", line)

        if line.strip():
            kept_lines.append(line.rstrip())

    images: list[Path] = []
    seen: set[str] = set()
    for token in image_tokens:
        resolved = _resolve_image_path(token, base_dir=base_dir)
        key = os.path.normcase(str(resolved))
        if key in seen:
            continue
        seen.add(key)
        images.append(resolved)

    text = "\n".join(kept_lines).strip()
    if not text and images:
        text = "请根据附图提取题意并输出 analysis_packet。"
    return text, images


def parse_requirement_inputs(*, requirement: str, requirement_file: str) -> tuple[str, list[Path]]:
    direct = str(requirement or "").strip()
    if direct:
        return direct, []

    file_path = Path(requirement_file) if requirement_file else None
    if file_path and file_path.exists():
        return parse_question_text(file_path.read_text(encoding="utf-8"), base_dir=file_path.parent)

    raise ValueError("请提供 --requirement 或 --requirement-file")
