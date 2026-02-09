from __future__ import annotations

from .grid_2x2 import grid_2x2
from .grid_3x3 import grid_3x3
from .hero_side import hero_side
from .left_right import left_right
from .left3_right3 import left3_right3
from .left4_right4 import left4_right4
from .types import SlotBBox, Template

TEMPLATE_FACTORIES = {
    "hero_side": hero_side,
    "left_right": left_right,
    "left3_right3": left3_right3,
    "left4_right4": left4_right4,
    "grid_2x2": grid_2x2,
    "grid_3x3": grid_3x3,
}


def build_template(template_type: str, params: dict | None = None) -> Template:
    factory = TEMPLATE_FACTORIES.get(template_type)
    if factory is None:
        raise KeyError(f"Unknown template: {template_type}")
    return factory(params or {})


TEMPLATE_REGISTRY: dict[str, Template] = {name: build_template(name) for name in TEMPLATE_FACTORIES}

__all__ = ["SlotBBox", "Template", "TEMPLATE_REGISTRY", "TEMPLATE_FACTORIES", "build_template"]
