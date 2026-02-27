from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


# MVP 项目根目录（本文件位于 MVP/pipeline/ 下，所以需要上跳一层）
MVP_ROOT = Path(__file__).resolve().parents[1]

# 配置目录：默认读取 configs/llm.yaml
CONFIG_DIR = MVP_ROOT / "configs"

# Prompt 目录
PROMPTS_DIR = MVP_ROOT / "prompts"

# 运行产物目录
RUNS_DIR = MVP_ROOT / "runs"

# 全局错误日志目录（集中记录 llm4 渲染报错）
ERROR_DIR = MVP_ROOT / "error"


def load_yaml(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_llm_yaml() -> dict[str, Any]:
    """
    读取 LLM 配置文件。

    优先级：
    1) MVP/configs/llm.yaml
    2) MVP/llm.yaml（兼容一些项目喜欢放在根目录）
    """

    candidates = [
        CONFIG_DIR / "llm.yaml",
        MVP_ROOT / "llm.yaml",
    ]
    for path in candidates:
        if path.exists():
            raw = load_yaml(path) or {}
            if isinstance(raw, dict):
                return raw
            return {}
    return {}
