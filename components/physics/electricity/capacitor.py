"""
电学组件库 - 静态可视化组件

包含基本的电学元件：电阻、电池、灯泡、开关
所有组件都是纯静态展示，无复杂计算
"""

from __future__ import annotations

from manim import *
from typing import Optional

class Capacitor(VGroup):
    """??????"""

    def __init__(
        self,
        width: float = 1.2,
        height: float = 0.8,
        color: str = WHITE,
        stroke_width: float = 4.0,
        **kwargs
    ):
        super().__init__(**kwargs)

        left_plate = Line(
            start=[-width/2, -height/2, 0],
            end=[-width/2, height/2, 0],
            color=color,
            stroke_width=stroke_width
        )

        right_plate = Line(
            start=[width/2, -height/2, 0],
            end=[width/2, height/2, 0],
            color=color,
            stroke_width=stroke_width
        )

        self.add(left_plate, right_plate)
