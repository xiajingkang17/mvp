"""
电学组件库 - 静态可视化组件

包含基本的电学元件：电阻、电池、灯泡、开关
所有组件都是纯静态展示，无复杂计算
"""

from __future__ import annotations

from manim import *
from typing import Optional

class Switch(VGroup):
    """?????"""

    def __init__(
        self,
        width: float = 2.0,
        height: float = 0.8,
        color: str = WHITE,
        stroke_width: float = 4.0,
        **kwargs
    ):
        super().__init__(**kwargs)

        left_terminal = Circle(
            radius=0.08,
            color=color,
            fill_color=color,
            fill_opacity=1.0
        ).shift([-width/2, 0, 0])

        left_wire = Line(
            start=[-width/2, 0, 0],
            end=[-width/4, 0, 0],
            color=color,
            stroke_width=stroke_width
        )

        right_wire = Line(
            start=[width/4, 0, 0],
            end=[width/2, 0, 0],
            color=color,
            stroke_width=stroke_width
        )

        right_terminal = Circle(
            radius=0.08,
            color=color,
            fill_color=color,
            fill_opacity=1.0
        ).shift([width/2, 0, 0])

        lever = Line(
            start=[-width/4, 0, 0],
            end=[width/4, height, 0],
            color=color,
            stroke_width=stroke_width
        )

        self.add(left_wire, right_wire, lever, left_terminal, right_terminal)
