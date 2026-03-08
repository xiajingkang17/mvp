from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


def slugify(text: str, *, max_len: int = 36) -> str:
    raw = re.sub(r"\s+", "_", str(text or "").strip())
    raw = re.sub(r"[^A-Za-z0-9_\-\u4e00-\u9fff]+", "", raw)
    raw = raw.strip("_")
    return (raw[:max_len] or "run").strip("_")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path

