from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any

from .config import MVP_ROOT, RUNS_DIR


def slugify(text: str, *, max_len: int = 48) -> str:
    s = re.sub(r"\s+", "_", text.strip())
    s = re.sub(r"[^A-Za-z0-9_\\-\\u4e00-\\u9fff]+", "", s)
    s = s.strip("_")
    return (s[:max_len] or "run").strip("_")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_requirement(
    *,
    requirement: str = "",
    requirement_file: str = "",
    run_dir: Path | None = None,
) -> str:
    """
    读取需求文本，优先级：
    1) --requirement
    2) --requirement-file
    3) <run_dir>/requirement.txt（如果存在）
    """

    if requirement and requirement.strip():
        return requirement.strip()

    if requirement_file:
        return Path(requirement_file).read_text(encoding="utf-8").strip()

    if run_dir is not None:
        req_path = run_dir / "requirement.txt"
        if req_path.exists():
            return req_path.read_text(encoding="utf-8").strip()

    raise SystemExit("requirement 为空：请用 -r 或 --requirement-file 提供，或指定含 requirement.txt 的 --run-dir。")


def ensure_run_dir(*, requirement: str, run_dir: str = "", requirement_file: str = "") -> Path:
    """
    若传入 --run-dir 则使用它；否则在 RUNS_DIR 下创建一个新的运行目录。
    """

    if run_dir:
        path = Path(run_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path

    # Case 约定：当 requirement_file 在 MVP/cases/<case_name>/... 下时，默认把产物落在 case 目录。
    if requirement_file:
        try:
            req_path = Path(requirement_file).resolve()
            cases_root = (MVP_ROOT / "cases").resolve()
            rel = req_path.relative_to(cases_root)
            if len(rel.parts) >= 2:
                case_dir = cases_root / rel.parts[0]
                case_dir.mkdir(parents=True, exist_ok=True)
                return case_dir
        except Exception:  # noqa: BLE001
            pass

    run_id = time.strftime("%Y%m%d_%H%M%S")
    slug = slugify(requirement)
    path = RUNS_DIR / f"{run_id}_{slug}"
    path.mkdir(parents=True, exist_ok=True)
    return path


def list_scenes(plan: dict[str, Any]) -> list[dict[str, Any]]:
    scenes = plan.get("scenes") or []
    if not isinstance(scenes, list):
        return []
    return [sc for sc in scenes if isinstance(sc, dict)]


def pick_scenes(plan: dict[str, Any], *, scene_id: str = "") -> list[dict[str, Any]]:
    scenes = list_scenes(plan)
    if not scene_id:
        return scenes
    wanted = scene_id.strip()
    return [sc for sc in scenes if str(sc.get("scene_id") or "").strip() == wanted]
