from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SlotBBox:
    """
    safe-area 坐标系内的归一化 bbox。

    坐标系：
    - cx, cy ∈ [0, 1]，其中 (0,0) 是 safe-area 左下角，(1,1) 是 safe-area 右上角
    - w, h ∈ (0, 1]
    """

    cx: float
    cy: float
    w: float
    h: float
    anchor: str = "C"  # 锚点：C/UL/UR/DL/DR/U/D/L/R


@dataclass(frozen=True)
class Template:
    type: str
    slots: dict[str, SlotBBox]
    slot_order: list[str]


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


def grid_2x2() -> Template:
    slots, order = _grid_slots(cols=2, rows=2)
    return Template(type="grid_2x2", slots=slots, slot_order=order)


def grid_3x3() -> Template:
    slots, order = _grid_slots(cols=3, rows=3)
    return Template(type="grid_3x3", slots=slots, slot_order=order)


TEMPLATE_REGISTRY: dict[str, Template] = {
    "hero_side": hero_side(),
    "left_right": left_right(),
    "grid_2x2": grid_2x2(),
    "grid_3x3": grid_3x3(),
}
