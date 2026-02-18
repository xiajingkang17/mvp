"""
电学组件库 - 静态可视化组件

包含基本的电学元件：电阻、电池、灯泡、开关
所有组件都是纯静态展示，无复杂计算
"""

from __future__ import annotations

from manim import *
from typing import Optional

class Bulb(VGroup):
    """?????"""

    def __init__(
        self,
        radius: float = 0.6,
        color: str = WHITE,
        stroke_width: float = 4.0,
        fill_color: str = YELLOW,
        fill_opacity: float = 0.3,
        **kwargs
    ):
        super().__init__(**kwargs)

        circle = Circle(
            radius=radius,
            color=color,
            stroke_width=stroke_width,
            fill_color=fill_color,
            fill_opacity=fill_opacity
        )

        cross1 = Line(
            start=[-radius * 0.5, radius * 0.5, 0],
            end=[radius * 0.5, -radius * 0.5, 0],
            color=color,
            stroke_width=stroke_width
        )

        cross2 = Line(
            start=[radius * 0.5, radius * 0.5, 0],
            end=[-radius * 0.5, -radius * 0.5, 0],
            color=color,
            stroke_width=stroke_width
        )

        self.add(circle, cross1, cross2)
