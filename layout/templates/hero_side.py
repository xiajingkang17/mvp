from __future__ import annotations

from layout.templates.types import SlotBBox, Template


def hero_side(params: dict | None = None) -> Template:
    _ = params  # Template geometry is fixed; only slot_scales is supported globally.

    hero_ratio = 0.66
    side_ratio = 1.0 - hero_ratio
    hero_cx = hero_ratio / 2.0
    side_cx = hero_ratio + side_ratio / 2.0

    slots = {
        "hero": SlotBBox(cx=hero_cx, cy=0.5, w=hero_ratio, h=1.0, anchor="C"),
        "side": SlotBBox(cx=side_cx, cy=0.5, w=side_ratio, h=1.0, anchor="UL"),
    }
    return Template(type="hero_side", slots=slots, slot_order=["hero", "side"])
