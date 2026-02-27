from __future__ import annotations

import math

import numpy as np
from manim import Arc, VGroup, WHITE


class ArcTrack(VGroup):
    """General arc track using center + radius + CCW start/end angles."""

    def __init__(
        self,
        center: tuple[float, float, float] = (0.0, 0.0, 0.0),
        radius: float = 1.0,
        start: float = 0.0,
        end: float = 90.0,
        color: str = WHITE,
        stroke_width: float = 4.0,
        **kwargs,
    ):
        super().__init__(**kwargs)

        center_arr = self._to_center3(center)
        start_rad = math.radians(start)
        end_rad = math.radians(end)
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

    @staticmethod
    def _to_center3(center: tuple[float, ...] | list[float] | np.ndarray) -> np.ndarray:
        arr = np.array(center, dtype=float).reshape(-1)
        if arr.size == 2:
            return np.array([arr[0], arr[1], 0.0], dtype=float)
        if arr.size >= 3:
            return np.array([arr[0], arr[1], arr[2]], dtype=float)
        return np.array([0.0, 0.0, 0.0], dtype=float)
