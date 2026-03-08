from __future__ import annotations

import os
from pathlib import Path

from .config import M4T_ROOT


def load_dotenv(path: str | os.PathLike[str] = ".env", *, override: bool = False) -> bool:
    env_path = Path(path)
    if not env_path.is_absolute():
        candidate = M4T_ROOT / env_path
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

