from __future__ import annotations

import math
import numpy as np
from manim import *
from typing import Optional, List, Tuple

class Weight(VGroup):
    """砝码组件。"""

    def __init__(
        self,
        width: float = 1.0,
        height: float = 1.5,
        hook_radius: float = 0.15,
        color: str = WHITE,
        stroke_width: float = 4.0,
        **kwargs
    ):
        super().__init__(**kwargs)

        body = Rectangle(
            width=width,
            height=height,
            stroke_color=color,
            stroke_width=stroke_width,
            fill_color=BLACK,
            fill_opacity=1.0
        )

        hook_y = height/2 + hook_radius
        hook_ring = Annulus(
            inner_radius=hook_radius * 0.6,
            outer_radius=hook_radius,
            color=color,
            stroke_width=stroke_width,
            fill_opacity=0
        ).shift([0, hook_y, 0])

        self.add(hook_ring, body)

