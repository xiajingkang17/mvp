from __future__ import annotations

from .grids import grid_2x2, grid_3x3
from .splits import hero_side, left_right
from .types import SlotBBox, Template

TEMPLATE_REGISTRY: dict[str, Template] = {
    "hero_side": hero_side(),
    "left_right": left_right(),
    "grid_2x2": grid_2x2(),
    "grid_3x3": grid_3x3(),
}

__all__ = ["SlotBBox", "Template", "TEMPLATE_REGISTRY"]
