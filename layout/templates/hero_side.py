from __future__ import annotations

from layout.params import clamp
from layout.templates.types import SlotBBox, Template


def hero_side(params: dict | None = None) -> Template:
    params = params or {}
    hero_ratio = params.get("hero_ratio", 0.66)
    side_ratio = params.get("side_ratio", None)
    if side_ratio is not None:
        try:
            hero_ratio = 1.0 - float(side_ratio)
        except (TypeError, ValueError):
            hero_ratio = 0.66
    hero_ratio = clamp(float(hero_ratio), 0.5, 0.8)
    side_ratio = 1.0 - hero_ratio
    hero_cx = hero_ratio / 2.0
    side_cx = hero_ratio + side_ratio / 2.0

    slots = {
        "hero": SlotBBox(cx=hero_cx, cy=0.5, w=hero_ratio, h=1.0, anchor="C"),
        "side": SlotBBox(cx=side_cx, cy=0.5, w=side_ratio, h=1.0, anchor="UL"),
    }
    return Template(type="hero_side", slots=slots, slot_order=["hero", "side"])
