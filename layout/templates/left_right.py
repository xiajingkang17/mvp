from __future__ import annotations

from layout.templates.types import SlotBBox, Template


def left_right(params: dict | None = None) -> Template:
    _ = params  # Template geometry is fixed; only slot_scales is supported globally.

    left_ratio = 0.5
    right_ratio = 1.0 - left_ratio
    left_cx = left_ratio / 2.0
    right_cx = left_ratio + right_ratio / 2.0

    slots = {
        "left": SlotBBox(cx=left_cx, cy=0.5, w=left_ratio, h=1.0, anchor="UL"),
        "right": SlotBBox(cx=right_cx, cy=0.5, w=right_ratio, h=1.0, anchor="UL"),
    }
    return Template(type="left_right", slots=slots, slot_order=["left", "right"])
