from __future__ import annotations

import math
import numpy as np
from manim import *
from typing import Dict, List, Optional, Tuple

class Block(VGroup):
    """滑块组件（矩形），内置语义锚点。"""

    def __init__(
        self,
        width: float = 1.5,
        height: float = 1.0,
        label: str = "m",
        label_color: str = WHITE,
        color: str = WHITE,
        stroke_width: float = 4.0,
        **kwargs
    ):
        super().__init__(**kwargs)
        self._anchor_points: Dict[str, VectorizedPoint] = {}

        body = Rectangle(
            width=width,
            height=height,
            stroke_color=color,
            stroke_width=stroke_width,
            fill_color=BLACK,
            fill_opacity=1.0
        )
        self.body = body

        self.add(body)
        self._init_anchors(width=width, height=height)

        if label:
            label_text = Tex(label, font_size=36, color=label_color)
            label_text.move_to(body.get_center())
            self.add(label_text)

    def _init_anchors(self, width: float, height: float) -> None:
        half_w = width / 2.0
        half_h = height / 2.0
        local_points = {
            "center": np.array([0.0, 0.0, 0.0]),
            "top_center": np.array([0.0, half_h, 0.0]),
            "bottom_center": np.array([0.0, -half_h, 0.0]),
            "left_center": np.array([-half_w, 0.0, 0.0]),
            "right_center": np.array([half_w, 0.0, 0.0]),
            "top_left": np.array([-half_w, half_h, 0.0]),
            "top_right": np.array([half_w, half_h, 0.0]),
            "bottom_left": np.array([-half_w, -half_h, 0.0]),
            "bottom_right": np.array([half_w, -half_h, 0.0]),
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
