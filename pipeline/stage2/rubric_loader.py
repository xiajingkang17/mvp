from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from ..core.config import PROMPTS_DIR


ReviewDomain = Literal["math", "physics"]

_PHYSICS_KEYWORDS = (
    "物理",
    "速度",
    "加速度",
    "位移",
    "受力",
    "轨道",
    "滑块",
    "小球",
    "小车",
    "粒子",
    "杆",
    "连杆",
    "绳",
    "摆",
    "摩擦",
    "碰撞",
    "圆周",
    "动能",
    "势能",
    "机械能",
    "弹簧",
    "质量",
    "电荷",
    "磁场",
    "电场",
    "particle",
    "track",
    "velocity",
    "acceleration",
    "force",
)


def _rubric_dir() -> Path:
    return PROMPTS_DIR / "review_rubrics"


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def infer_review_domain(*, requirement: str, analysis_packet: dict[str, Any] | None) -> ReviewDomain:
    parts = [str(requirement or "").strip()]
    if isinstance(analysis_packet, dict):
        parts.append(json.dumps(analysis_packet, ensure_ascii=False))
    haystack = "\n".join(part for part in parts if part).lower()
    if any(keyword.lower() in haystack for keyword in _PHYSICS_KEYWORDS):
        return "physics"
    return "math"


def load_review_rubrics(*, domain: ReviewDomain) -> dict[str, str]:
    folder = _rubric_dir()
    common = _read_text(folder / "common_teaching_visual_rules.md")
    domain_filename = "math_teaching_visual_rules.md" if domain == "math" else "physics_teaching_visual_rules.md"
    domain_rules = _read_text(folder / domain_filename)
    return {
        "common": common,
        "domain": domain,
        "domain_rules": domain_rules,
    }


def build_review_rubric_block(*, requirement: str, analysis_packet: dict[str, Any] | None) -> tuple[ReviewDomain, str]:
    domain = infer_review_domain(requirement=requirement, analysis_packet=analysis_packet)
    rubrics = load_review_rubrics(domain=domain)
    block = (
        "[教学图公共规则]\n"
        f"{rubrics['common']}\n\n"
        f"[当前学科补充规则: {domain}]\n"
        f"{rubrics['domain_rules']}\n"
    )
    return domain, block
