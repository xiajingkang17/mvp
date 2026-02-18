"""
电学组件库 - 静态可视化组件

包含基本的电学元件：电阻、电池、灯泡、开关
所有组件都是纯静态展示，无复杂计算
"""

from __future__ import annotations

from manim import *
from typing import Optional

class Resistor(VGroup):
    """?????"""

    def __init__(
        self,
        width: float = 2.0,
        height: float = 0.5,
        lead_length: float = 0.8,
        color: str = WHITE,
        stroke_width: float = 4.0,
        **kwargs
    ):
        super().__init__(**kwargs)

        resistor_body = Rectangle(
            width=width,
            height=height,
            stroke_color=color,
            stroke_width=stroke_width,
            fill_color=BLACK,
            fill_opacity=1.0
        )

        left_lead = Line(
            start=[-width/2 - lead_length, 0, 0],
            end=[-width/2, 0, 0],
            color=color,
            stroke_width=stroke_width
        )

        right_lead = Line(
            start=[width/2, 0, 0],
            end=[width/2 + lead_length, 0, 0],
            color=color,
            stroke_width=stroke_width
        )

        self.add(left_lead, resistor_body, right_lead)
