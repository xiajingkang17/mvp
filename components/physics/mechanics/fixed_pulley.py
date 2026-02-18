from __future__ import annotations

import math
import numpy as np
from manim import *
from typing import Dict, List, Optional, Tuple
from .pulley import Pulley

class FixedPulley(Pulley):
    """定滑轮组件，内置语义锚点。"""

    def __init__(
        self,
        radius: float = 0.5,
        rod_length: float = 1.0,
        color: str = WHITE,
        stroke_width: float = 4.0,
        **kwargs
    ):
        super(VGroup, self).__init__(**kwargs)
        self._anchor_points: Dict[str, VectorizedPoint] = {}

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
        self._init_anchors(radius=radius, rod_length=rod_length)

    def _init_anchors(self, radius: float, rod_length: float) -> None:
        local_points = {
            "center": np.array([0.0, 0.0, 0.0]),
            "left": np.array([-radius, 0.0, 0.0]),
            "right": np.array([radius, 0.0, 0.0]),
            "support_top": np.array([0.0, radius * 1.5 + rod_length, 0.0]),
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
