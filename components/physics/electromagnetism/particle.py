from __future__ import annotations

from typing import Dict, List

import numpy as np
from manim import BLACK, Circle, Tex, VectorizedPoint, VGroup, WHITE


class Particle(VGroup):
    """Charged-particle style marker for electromagnetism scenes."""

    def __init__(
        self,
        radius: float = 0.16,
        label: str = "",
        label_color: str = WHITE,
        color: str = WHITE,
        stroke_width: float = 4.0,
        fill_color: str = BLACK,
        fill_opacity: float = 1.0,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self._anchor_points: Dict[str, VectorizedPoint] = {}

        body = Circle(
            radius=float(radius),
            stroke_color=color,
            stroke_width=float(stroke_width),
            fill_color=fill_color,
            fill_opacity=float(fill_opacity),
        )
        self.body = body
        self.add(body)
        self._init_anchors(radius=float(radius))

        if label:
            label_text = Tex(str(label), font_size=30, color=label_color)
            label_text.move_to(body.get_center())
            self.add(label_text)

    def _init_anchors(self, radius: float) -> None:
        r = float(radius)
        local_points = {
            "center": np.array([0.0, 0.0, 0.0]),
            "top": np.array([0.0, r, 0.0]),
            "bottom": np.array([0.0, -r, 0.0]),
            "left": np.array([-r, 0.0, 0.0]),
            "right": np.array([r, 0.0, 0.0]),
            "top_center": np.array([0.0, r, 0.0]),
            "bottom_center": np.array([0.0, -r, 0.0]),
            "left_center": np.array([-r, 0.0, 0.0]),
            "right_center": np.array([r, 0.0, 0.0]),
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
