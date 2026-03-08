from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


# config.py 位于 Manim4Teach/pipeline/core，下两级才是项目根目录 Manim4Teach
M4T_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = M4T_ROOT / "configs"
PROMPTS_DIR = M4T_ROOT / "prompts"
RUNS_DIR = M4T_ROOT / "runs"


def load_yaml(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_llm_yaml() -> dict[str, Any]:
    candidates = [
        CONFIG_DIR / "llm.yaml",
        M4T_ROOT / "llm.yaml",
    ]
    for path in candidates:
        if not path.exists():
            continue
        raw = load_yaml(path) or {}
        if isinstance(raw, dict):
            return raw
    return {}
