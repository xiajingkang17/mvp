from __future__ import annotations

import math
import numpy as np
from manim import *
from typing import Optional, List, Tuple
from .pulley import Pulley

class MovablePulley(Pulley):
    """动滑轮组件。"""

    def __init__(
        self,
        radius: float = 0.5,
        hook_length: float = 0.6,
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

        hook_start = np.array([0, -radius * 0.8, 0])
        hook_end = np.array([0, -radius * 0.8 - hook_length, 0])

        hook_line = Line(
            start=hook_start,
            end=hook_end,
            color=color,
            stroke_width=stroke_width
        )

        hook_curve = Arc(
            radius=hook_length * 0.2,
            start_angle=PI/2,
            angle=PI,
            color=color,
            stroke_width=stroke_width
        )
        hook_curve.move_to(hook_end)

        self.add(base_pulley, hook_line, hook_curve)
