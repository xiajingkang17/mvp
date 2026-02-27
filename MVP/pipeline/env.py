from __future__ import annotations

import os
from pathlib import Path

from .config import MVP_ROOT


def load_dotenv(path: str | os.PathLike[str] = ".env", *, override: bool = False) -> bool:
    """
    从 `.env` 读取环境变量并写入到 `os.environ`。

    - 支持 `KEY=VALUE`、`export KEY=VALUE`
    - 忽略空行与 `#` 注释
    - 支持单引号/双引号包裹 VALUE
    - 默认不覆盖已存在的环境变量（override=False）

    搜索策略：
    - 若 path 是相对路径：优先在 MVP_ROOT 下查找（让 MVP 作为独立项目时行为稳定）
    - 若 MVP_ROOT 下不存在，再尝试当前工作目录
    """

    env_path = Path(path)
    if not env_path.is_absolute():
        candidate = MVP_ROOT / env_path
        if candidate.exists():
            env_path = candidate

    if not env_path.exists():
        return False

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        if line.startswith("export "):
            line = line[len("export ") :].strip()

        if "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            continue

        if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
            value = value[1:-1]

        if not override and key in os.environ:
            continue

        os.environ[key] = value

    return True
