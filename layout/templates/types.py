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

