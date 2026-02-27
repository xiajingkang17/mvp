from __future__ import annotations

import numpy as np
from manim import Circle, Tex, VectorizedPoint, VGroup, WHITE, BLACK
from typing import Dict, List


class Ball(VGroup):
    """小球组件（圆形），内置语义锚点。"""

    def __init__(
        self,
        radius: float = 0.4,
        label: str = "",
        label_color: str = WHITE,
        color: str = WHITE,
        stroke_width: float = 4.0,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self._anchor_points: Dict[str, VectorizedPoint] = {}

        body = Circle(
            radius=radius,
            stroke_color=color,
            stroke_width=stroke_width,
            fill_color=BLACK,
            fill_opacity=1.0,
        )
        self.body = body
        self.add(body)
        self._init_anchors(radius=radius)

        if label:
            label_text = Tex(label, font_size=32, color=label_color)
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
        if name not in self._anchor_points:
            available = ", ".join(self.list_anchors())
            raise ValueError(f"Unknown anchor '{name}'. Available: {available}")
        return np.array(self._anchor_points[name].get_center())
