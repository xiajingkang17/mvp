from __future__ import annotations

from manim import *

from .pulley import Pulley


class FixedPulley(Pulley):
    """定滑轮组件。"""

    def __init__(
        self,
        radius: float = 0.5,
        rod_length: float = 1.0,
        color: str = WHITE,
        stroke_width: float = 4.0,
        **kwargs
    ):
        super(VGroup, self).__init__(**kwargs)

        base_pulley = Pulley(
            radius=radius,
            color=color,
            stroke_width=stroke_width
        )
        self.base_pulley = base_pulley

        fixed_rod = Line(
            start=[0, radius * 1.5, 0],
            end=[0, radius * 1.5 + rod_length, 0],
            color=color,
            stroke_width=stroke_width
        )
        self.fixed_rod = fixed_rod

        self.add(base_pulley, fixed_rod)
