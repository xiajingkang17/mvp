from __future__ import annotations

import math
from typing import Dict, List

import numpy as np
from manim import DEGREES, Line, VectorizedPoint, VGroup, WHITE


class Arrow(VGroup):
    """Open-head arrow component (`->`) using line segments."""

    def __init__(
        self,
        length: float = 1.8,
        angle: float = 0.0,
        head_length: float = 0.28,
        head_angle: float = 26.0,
        color: str = WHITE,
        stroke_width: float = 4.0,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self._anchor_points: Dict[str, VectorizedPoint] = {}

        total_length = max(1e-3, float(length))
        tip_arm_length = max(1e-3, min(float(head_length), total_length * 0.8))
        tip_angle_deg = max(5.0, min(85.0, float(head_angle)))
        tip_angle_rad = math.radians(tip_angle_deg)

        half = 0.5 * total_length
        start = np.array([-half, 0.0, 0.0], dtype=float)
        tip = np.array([half, 0.0, 0.0], dtype=float)

        shaft = Line(start=start, end=tip, color=color, stroke_width=stroke_width)
        upper_dir = np.array([-math.cos(tip_angle_rad), math.sin(tip_angle_rad), 0.0], dtype=float)
        lower_dir = np.array([-math.cos(tip_angle_rad), -math.sin(tip_angle_rad), 0.0], dtype=float)
        head_upper = Line(start=tip, end=tip + tip_arm_length * upper_dir, color=color, stroke_width=stroke_width)
        head_lower = Line(start=tip, end=tip + tip_arm_length * lower_dir, color=color, stroke_width=stroke_width)

        self.add(shaft, head_upper, head_lower)
        self._init_anchors(start=start, tip=tip)

        if float(angle) != 0.0:
            self.rotate(float(angle) * DEGREES, about_point=np.array([0.0, 0.0, 0.0]))

    def _init_anchors(self, *, start: np.ndarray, tip: np.ndarray) -> None:
        center = 0.5 * (start + tip)
        local_points = {
            "center": center,
            "start": start,
            "end": tip,
            "tip": tip,
        }
        for name, point in local_points.items():
            anchor = VectorizedPoint(point)
            self._anchor_points[name] = anchor
            self.add(anchor)

    def list_anchors(self) -> List[str]:
        return list(self._anchor_points.keys())

    def get_anchor(self, name: str) -> np.ndarray:
        key = str(name).strip()
        if key not in self._anchor_points:
            available = ", ".join(self.list_anchors())
            raise ValueError(f"Unknown anchor '{name}'. Available: {available}")
        return np.array(self._anchor_points[key].get_center())
