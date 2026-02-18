from __future__ import annotations

import math
import numpy as np
from manim import *
from typing import Optional, List, Tuple

class Hinge(VGroup):
    """铰链组件。"""

    def __init__(
        self,
        radius: float = 0.2,
        color: str = WHITE,
        stroke_width: float = 4.0,
        **kwargs
    ):
        super().__init__(**kwargs)

        outer_ring = Circle(
            radius=radius,
            color=color,
            stroke_width=stroke_width,
            fill_color=BLACK,
            fill_opacity=1.0
        )

        center_dot = Dot(
            point=ORIGIN,
            radius=0.04,
            color=color
        )

        self.add(outer_ring, center_dot)


