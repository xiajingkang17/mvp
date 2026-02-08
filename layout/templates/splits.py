from __future__ import annotations

from layout.templates.types import SlotBBox, Template


def hero_side() -> Template:
    slots = {
        "hero": SlotBBox(cx=0.33, cy=0.5, w=0.66, h=1.0, anchor="C"),
        "side": SlotBBox(cx=0.83, cy=0.5, w=0.34, h=1.0, anchor="UL"),
    }
    return Template(type="hero_side", slots=slots, slot_order=["hero", "side"])


def left_right() -> Template:
    slots = {
        "left": SlotBBox(cx=0.25, cy=0.5, w=0.5, h=1.0, anchor="UL"),
        "right": SlotBBox(cx=0.75, cy=0.5, w=0.5, h=1.0, anchor="UL"),
    }
    return Template(type="left_right", slots=slots, slot_order=["left", "right"])

