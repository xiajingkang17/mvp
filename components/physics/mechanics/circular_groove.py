from __future__ import annotations

import math
import numpy as np
from manim import *
from typing import Optional, List, Tuple

class CircularGroove(VGroup):
    """圆形轨道组件。"""

    def __init__(
        self,
        radius: float = 2.0,
        groove_width: float = 0.3,
        color: str = WHITE,
        stroke_width: float = 4.0,
        **kwargs
    ):
        super().__init__(**kwargs)

        outer_circle = Circle(
            radius=radius + groove_width/2,
            color=color,
            stroke_width=stroke_width,
            fill_opacity=0
        )

        inner_circle = Circle(
            radius=radius - groove_width/2,
            color=color,
            stroke_width=stroke_width,
            fill_opacity=0
        )

        fill_region = Annulus(
            inner_radius=radius - groove_width/2,
            outer_radius=radius + groove_width/2,
            color=color,
            stroke_width=0,
            fill_opacity=0.2
        )

        self.add(outer_circle, inner_circle, fill_region)
