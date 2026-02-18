from __future__ import annotations

import math
from typing import Dict, List

import numpy as np
from manim import Arc, VGroup, VectorizedPoint, WHITE


class SemicircleGroove(VGroup):
    """Semicircle track drawn as a single arc curve."""

    def __init__(
        self,
        center: tuple[float, float, float] = (0.0, 0.0, 0.0),
        radius: float = 2.0,
        start_angle: float = 0.0,
        end_angle: float = 180.0,
        groove_width: float = 0.3,
        color: str = WHITE,
        stroke_width: float = 4.0,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self._anchor_points: Dict[str, VectorizedPoint] = {}

        _ = groove_width  # legacy compatibility, no longer used for rendering

        center_arr = self._to_center3(center)
        start_rad = math.radians(start_angle)
        end_rad = math.radians(end_angle)
        sweep = end_rad - start_rad
        if sweep <= 0:
            sweep += 2.0 * math.pi

        arc = Arc(
            radius=radius,
            start_angle=start_rad,
            angle=sweep,
            color=color,
            stroke_width=stroke_width,
        )
        arc.shift(center_arr)
        self.arc = arc
        self.add(arc)
        self._init_anchors(center=center_arr, radius=radius, start_rad=start_rad, end_rad=start_rad + sweep)

    @staticmethod
    def _to_center3(center: tuple[float, ...] | list[float] | np.ndarray) -> np.ndarray:
        arr = np.array(center, dtype=float).reshape(-1)
        if arr.size == 2:
            return np.array([arr[0], arr[1], 0.0], dtype=float)
        if arr.size >= 3:
            return np.array([arr[0], arr[1], arr[2]], dtype=float)
        return np.array([0.0, 0.0, 0.0], dtype=float)

    def _init_anchors(self, *, center: np.ndarray, radius: float, start_rad: float, end_rad: float) -> None:
        mid_rad = 0.5 * (start_rad + end_rad)
        points = {
            "center": np.array(center),
            "start": np.array([center[0] + radius * math.cos(start_rad), center[1] + radius * math.sin(start_rad), 0.0]),
            "end": np.array([center[0] + radius * math.cos(end_rad), center[1] + radius * math.sin(end_rad), 0.0]),
            "mid": np.array([center[0] + radius * math.cos(mid_rad), center[1] + radius * math.sin(mid_rad), 0.0]),
            "left_end": np.array([center[0] - radius, center[1], 0.0]),
            "right_end": np.array([center[0] + radius, center[1], 0.0]),
            "top": np.array([center[0], center[1] + radius, 0.0]),
            "bottom": np.array([center[0], center[1] - radius, 0.0]),
        }
        for name, point in points.items():
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
