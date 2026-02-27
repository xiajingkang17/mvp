from __future__ import annotations

from layout.templates.types import SlotBBox, Template


def left4_right4(params: dict | None = None) -> Template:
    _ = params  # Template geometry is fixed; only slot_scales is supported globally.

    slots: dict[str, SlotBBox] = {}
    slot_order: list[str] = []

    col_w = 0.5
    row_h = 0.25
    left_cx = 0.25
    right_cx = 0.75

    for i in range(4):
        cy = 1.0 - (i + 0.5) * row_h
        left_name = f"left{i+1}"
        right_name = f"right{i+1}"

        slots[left_name] = SlotBBox(cx=left_cx, cy=cy, w=col_w, h=row_h, anchor="UL")
        slots[right_name] = SlotBBox(cx=right_cx, cy=cy, w=col_w, h=row_h, anchor="UL")
        slot_order.extend([left_name, right_name])

    return Template(type="left4_right4", slots=slots, slot_order=slot_order)
