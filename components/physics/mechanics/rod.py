from __future__ import annotations

import math
import numpy as np
from manim import *
from typing import Dict, List, Optional, Tuple

class Rod(VGroup):
    """刚性杆组件，内置语义锚点。"""

    def __init__(
        self,
        length: float = 4.0,
        thickness: float = 0.15,
        color: str = WHITE,
        stroke_width: float = 4.0,
        **kwargs
    ):
        super().__init__(**kwargs)
        self._anchor_points: Dict[str, VectorizedPoint] = {}

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
        self._init_anchors(length=length)

    def _init_anchors(self, length: float) -> None:
        half_len = length / 2.0
        local_points = {
            "center": np.array([0.0, 0.0, 0.0]),
            "start": np.array([-half_len, 0.0, 0.0]),
            "end": np.array([half_len, 0.0, 0.0]),
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
