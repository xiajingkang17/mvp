"""
电学组件库 - 静态可视化组件

包含基本的电学元件：电阻、电池、灯泡、开关
所有组件都是纯静态展示，无复杂计算
"""

from __future__ import annotations

from manim import *
from typing import Optional

class Battery(VGroup):
    """?????"""

    def __init__(
        self,
        width: float = 1.5,
        height_long: float = 1.2,
        height_short: float = 0.6,
        color: str = WHITE,
        stroke_width: float = 4.0,
        show_labels: bool = True,
        **kwargs
    ):
        super().__init__(**kwargs)

        positive_plate = Line(
            start=[-width/2, -height_long/2, 0],
            end=[-width/2, height_long/2, 0],
            color=color,
            stroke_width=stroke_width
        )

        negative_plate = Line(
            start=[width/2, -height_short/2, 0],
            end=[width/2, height_short/2, 0],
            color=color,
            stroke_width=stroke_width
        )

        self.add(positive_plate, negative_plate)

        if show_labels:
            plus_sign = Tex(
                r"+",
                font_size=48,
                color=color
            ).next_to(positive_plate, UP, buff=0.2)

            minus_sign = Tex(
                r"-",
                font_size=48,
                color=color
            ).next_to(negative_plate, UP, buff=0.2)

            self.add(plus_sign, minus_sign)
