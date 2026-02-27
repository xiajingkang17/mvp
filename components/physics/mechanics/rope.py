from __future__ import annotations

import math
import numpy as np
from manim import *
from typing import Dict, List, Optional, Tuple

class Rope(VGroup):
    """绳子组件，内置语义锚点。"""

    def __init__(
        self,
        length: float = 4.0,
        angle: float = 0,
        color: str = GRAY,
        stroke_width: float = 3.0,
        **kwargs
    ):
        super().__init__(**kwargs)
        self._anchor_points: Dict[str, VectorizedPoint] = {}

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
        self._init_anchors(start_point=start_point, end_point=end_point)

    def _init_anchors(self, start_point: np.ndarray, end_point: np.ndarray) -> None:
        center_point = (start_point + end_point) / 2.0
        local_points = {
            "center": center_point,
            "start": start_point,
            "end": end_point,
        }
        for name, point in local_points.items():
            anchor = VectorizedPoint(np.array(point))
            self._anchor_points[name] = anchor
            self.add(anchor)

    def list_anchors(self) -> List[str]:
        return list(self._anchor_points.keys())

    def get_anchor(self, name: str) -> np.ndarray:
        if name not in self._anchor_points:
            available = ", ".join(self.list_anchors())
            raise ValueError(f"Unknown anchor '{name}'. Available: {available}")
        return np.array(self._anchor_points[name].get_center())
