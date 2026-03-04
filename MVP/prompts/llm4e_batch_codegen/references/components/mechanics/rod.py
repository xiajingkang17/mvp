from __future__ import annotations

from manim import *


class Rod(VGroup):
    """刚性杆组件。"""

    def __init__(
        self,
        length: float = 4.0,
        thickness: float = 0.15,
        color: str = WHITE,
        stroke_width: float = 4.0,
        **kwargs
    ):
        super().__init__(**kwargs)

        rod = Rectangle(
            width=length,
            height=thickness,
            stroke_color=color,
            stroke_width=stroke_width,
            fill_color=BLACK,
            fill_opacity=1.0
        )
        self.rod = rod

        self.add(rod)
