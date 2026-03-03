from __future__ import annotations

import sys
from pathlib import Path

if __package__ in {None, ""}:
    MVP_ROOT = Path(__file__).resolve().parents[1]
    if str(MVP_ROOT) not in sys.path:
        sys.path.insert(0, str(MVP_ROOT))

from pipeline.run_llm4 import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main("zhipu"))
