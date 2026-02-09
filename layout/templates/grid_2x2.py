from __future__ import annotations

from layout.templates.types import SlotBBox, Template


def _grid_slots(cols: int, rows: int) -> tuple[dict[str, SlotBBox], list[str]]:
    slots: dict[str, SlotBBox] = {}
    order: list[str] = []

    letters = "abcdefghijklmnopqrstuvwxyz"
    idx = 0
    cell_w = 1.0 / cols
    cell_h = 1.0 / rows
    for r in range(rows):
        for c in range(cols):
            name = letters[idx]
            idx += 1
            cx = (c + 0.5) * cell_w
            cy = 1.0 - (r + 0.5) * cell_h
            slots[name] = SlotBBox(cx=cx, cy=cy, w=cell_w, h=cell_h, anchor="C")
            order.append(name)
    return slots, order


def grid_2x2(params: dict | None = None) -> Template:
    slots, order = _grid_slots(cols=2, rows=2)
    return Template(type="grid_2x2", slots=slots, slot_order=order)
