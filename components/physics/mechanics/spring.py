from __future__ import annotations

import math
import numpy as np
from manim import *
from typing import Dict, List, Optional, Tuple

class Spring(VGroup):
    """弹簧组件，内置语义锚点。"""

    def __init__(
        self,
        length: float = 4.0,
        height: float = 0.6,
        num_coils: int = 8,
        end_length: float = 0.5,
        color: str = WHITE,
        stroke_width: float = 3.0,
        **kwargs
    ):
        super().__init__(**kwargs)
        self._anchor_points: Dict[str, VectorizedPoint] = {}

        coil_width = (length - 2 * end_length) / num_coils

        left_end = Line(
            start=[-length/2, 0, 0],
            end=[-length/2 + end_length, 0, 0],
            color=color,
            stroke_width=stroke_width
        )
        self.left_end_line = left_end

        zigzag_points = [[-length/2 + end_length, 0, 0]]

        for i in range(num_coils):
            x_start = -length/2 + end_length + i * coil_width
            zigzag_points.append([x_start + coil_width/2, height/2, 0])
            zigzag_points.append([x_start + coil_width, -height/2, 0])

        zigzag_points.append([length/2 - end_length, 0, 0])

        zigzag = VMobject()
        zigzag.set_points_as_corners(zigzag_points)
        zigzag.set_color(color)
        zigzag.set_stroke(width=stroke_width)
        self.zigzag = zigzag

        right_end = Line(
            start=[length/2 - end_length, 0, 0],
            end=[length/2, 0, 0],
            color=color,
            stroke_width=stroke_width
        )
        self.right_end_line = right_end

        self.add(left_end, zigzag, right_end)
        self._init_anchors(length=length, end_length=end_length)

    def _init_anchors(self, length: float, end_length: float) -> None:
        half = length / 2.0
        local_points = {
            "center": np.array([0.0, 0.0, 0.0]),
            "start": np.array([-half, 0.0, 0.0]),
            "end": np.array([half, 0.0, 0.0]),
            "coil_start": np.array([-half + end_length, 0.0, 0.0]),
            "coil_end": np.array([half - end_length, 0.0, 0.0]),
        }
        for name, point in local_points.items():
            anchor = VectorizedPoint(point)
            self._anchor_points[name] = anchor
            self.add(anchor)

    def list_anchors(self) -> List[str]:
        return list(self._anchor_points.keys())

    def get_anchor(self, name: str) -> np.ndarray:
        if name not in self._anchor_points:
            available = ", ".join(self.list_anchors())
            raise ValueError(f"Unknown anchor '{name}'. Available: {available}")
        return np.array(self._anchor_points[name].get_center())
