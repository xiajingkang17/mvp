from __future__ import annotations

from functools import lru_cache
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from schema.scene_plan_models import ObjectSpec


@dataclass(frozen=True)
class ComponentDefaults:
    font: str
    text_font_size: int
    bullet_font_size: int
    formula_font_size: int


class Component(ABC):
    type_name: str

    @abstractmethod
    def build(self, spec: ObjectSpec, *, defaults: ComponentDefaults):
        raise NotImplementedError


def _style_get(spec: ObjectSpec, key: str, default: Any) -> Any:
    if key in spec.style:
        return spec.style[key]
    return default


def _pick_font(candidates: list[str], available_fonts: list[str]) -> str | None:
    if not available_fonts:
        return None

    exact = {f.lower(): f for f in available_fonts}
    for candidate in candidates:
        if not candidate:
            continue
        hit = exact.get(candidate.lower())
        if hit:
            return hit

    lowered = [(f.lower(), f) for f in available_fonts]
    for candidate in candidates:
        if not candidate:
            continue
        needle = candidate.lower()
        for lower_name, original_name in lowered:
            if needle in lower_name:
                return original_name
    return None


@lru_cache(maxsize=16)
def resolve_text_font(preferred: str | None) -> str:
    fallback_candidates = [
        preferred or "",
        "Microsoft YaHei",
        "Microsoft YaHei UI",
        "SimHei",
        "SimSun",
        "Noto Sans CJK SC",
        "Source Han Sans SC",
        "Arial",
    ]

    try:
        from manimpango import list_fonts

        available_fonts = list_fonts()
        selected = _pick_font(fallback_candidates, available_fonts)
        if selected:
            return selected
    except Exception:  # noqa: BLE001
        pass

    return preferred or "Arial"

