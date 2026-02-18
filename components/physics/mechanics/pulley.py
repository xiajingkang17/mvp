from __future__ import annotations

import math
import numpy as np
from manim import *
from typing import Optional, List, Tuple

class Pulley(VGroup):
    """滑轮组件。"""

    def __init__(
        self,
        radius: float = 0.5,
        rod_angle: float = 90 * DEGREES,
        color: str = WHITE,
        stroke_width: float = 4.0,
        **kwargs
    ):
        super().__init__(**kwargs)

        wheel = Circle(
            radius=radius,
            color=color,
            stroke_width=stroke_width,
            fill_color=BLACK,
            fill_opacity=1.0
        )

        axle = Dot(
            point=ORIGIN,
            radius=0.05,
            color=color
        )

        rod_length = radius * 1.5
        rod = Line(
            start=ORIGIN,
            end=RIGHT * rod_length,
            color=color,
            stroke_width=stroke_width
        )

        rod.rotate(rod_angle, about_point=ORIGIN)

        self.add(rod, wheel, axle)

        self.wheel = wheel
        self.axle = axle
        self.rod = rod
