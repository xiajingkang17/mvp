from __future__ import annotations

import os
from pathlib import Path


def load_dotenv(path: str | os.PathLike[str] = ".env", *, override: bool = False) -> bool:
    """
    从 `.env` 读取环境变量并写入到 `os.environ`。

    - 支持 `KEY=VALUE`、`export KEY=VALUE`
    - 忽略空行与 `#` 注释
    - 支持用单引号/双引号包裹 VALUE
    - 默认不覆盖已存在的环境变量（override=False）
    """

    env_path = Path(path)
    if not env_path.is_absolute() and not env_path.exists():
        try:
            from pipeline.config import ROOT_DIR

            candidate = ROOT_DIR / env_path
            if candidate.exists():
                env_path = candidate
        except Exception:  # noqa: BLE001
            pass

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
