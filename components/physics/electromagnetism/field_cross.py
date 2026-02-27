from __future__ import annotations

import math
from typing import Dict, List

import numpy as np
from manim import DEGREES, Line, VectorizedPoint, VGroup, WHITE


class FieldCross(VGroup):
    """Cross marker (x) used for into-screen magnetic-field symbols."""

    def __init__(
        self,
        size: float = 0.22,
        angle: float = 0.0,
        color: str = WHITE,
        stroke_width: float = 4.0,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self._anchor_points: Dict[str, VectorizedPoint] = {}

        half = max(1e-3, float(size))
        line1 = Line(
            start=np.array([-half, -half, 0.0]),
            end=np.array([half, half, 0.0]),
            color=color,
            stroke_width=float(stroke_width),
        )
        line2 = Line(
            start=np.array([-half, half, 0.0]),
            end=np.array([half, -half, 0.0]),
            color=color,
            stroke_width=float(stroke_width),
        )
        self.add(line1, line2)

        if float(angle) != 0.0:
            self.rotate(float(angle) * DEGREES, about_point=np.array([0.0, 0.0, 0.0]))

        self._init_anchors(half=half, angle=float(angle))

    def _init_anchors(self, *, half: float, angle: float) -> None:
        theta = math.radians(float(angle))
        c = math.cos(theta)
        s = math.sin(theta)

        def _rot(x: float, y: float) -> np.ndarray:
            return np.array([c * x - s * y, s * x + c * y, 0.0], dtype=float)

        points = {
            "center": np.array([0.0, 0.0, 0.0], dtype=float),
            "top": _rot(0.0, half),
            "bottom": _rot(0.0, -half),
            "left": _rot(-half, 0.0),
            "right": _rot(half, 0.0),
            "top_center": _rot(0.0, half),
            "bottom_center": _rot(0.0, -half),
            "left_center": _rot(-half, 0.0),
            "right_center": _rot(half, 0.0),
        }
        for name, point in points.items():
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
