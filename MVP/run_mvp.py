from __future__ import annotations

import sys
from pathlib import Path

# 允许：
# - 从父目录执行：python MVP/run_mvp.py
# - 在 MVP 目录内执行：python run_mvp.py
MVP_ROOT = Path(__file__).resolve().parent
if str(MVP_ROOT) not in sys.path:
    sys.path.insert(0, str(MVP_ROOT))

from pipeline.run_mvp import main  # noqa: E402


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        raise

