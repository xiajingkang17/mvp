from __future__ import annotations

from layout.params import normalize_weights
from layout.templates.types import SlotBBox, Template


def left3_right3(params: dict | None = None) -> Template:
    """
    左 3 格 + 右 3 格（共 6 格）。

    - 两列等宽：左列、右列各占 50%
    - 每列 3 行等高：每格高度 1/3
    - 插槽命名：left1..left3（从上到下）、right1..right3（从上到下）
    """

    params = params or {}
    weights = params.get("row_weights", [1.0 / 3.0] * 3)
    if not isinstance(weights, list) or len(weights) != 3:
        weights = [1.0 / 3.0] * 3
    weights = normalize_weights(weights)

    slots: dict[str, SlotBBox] = {}
    slot_order: list[str] = []

    col_w = 0.5
    left_cx = 0.25
    right_cx = 0.75

    cumulative = 0.0
    for i in range(3):
        row_h = weights[i]
        cy = 1.0 - (cumulative + row_h / 2.0)
        left_name = f"left{i+1}"
        right_name = f"right{i+1}"

        slots[left_name] = SlotBBox(cx=left_cx, cy=cy, w=col_w, h=row_h, anchor="UL")
        slots[right_name] = SlotBBox(cx=right_cx, cy=cy, w=col_w, h=row_h, anchor="UL")

        slot_order.append(left_name)
        slot_order.append(right_name)
        cumulative += row_h

    return Template(type="left3_right3", slots=slots, slot_order=slot_order)
