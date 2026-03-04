from __future__ import annotations

import math
import numpy as np
from manim import *


class Rope(VGroup):
    """绳子组件。"""

    def __init__(
        self,
        length: float = 4.0,
        angle: float = 0,
        color: str = GRAY,
        stroke_width: float = 3.0,
        **kwargs
    ):
        super().__init__(**kwargs)

        angle_rad = angle * DEGREES
        start_point = np.array([
            -length/2 * math.cos(angle_rad),
            -length/2 * math.sin(angle_rad),
            0
        ])
        end_point = np.array([
            length/2 * math.cos(angle_rad),
            length/2 * math.sin(angle_rad),
            0
        ])

        rope = Line(
            start=start_point,
            end=end_point,
            color=color,
            stroke_width=stroke_width
        )
        self.rope = rope

        self.add(rope)
