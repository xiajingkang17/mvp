from __future__ import annotations

import math
import numpy as np
from manim import *
from typing import Dict, List, Optional, Tuple

class Cart(VGroup):
    """小车组件，内置语义锚点。"""

    def __init__(
        self,
        width: float = 2.5,
        height: float = 0.8,
        wheel_radius: float = 0.3,
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
        ).shift([0, height / 2.0, 0])
        self.body = body

        left_wheel = Circle(
            radius=wheel_radius,
            color=color,
            stroke_width=stroke_width,
            fill_color=BLACK,
            fill_opacity=1.0
        ).shift([
            -width/4,
            -wheel_radius,
            0
        ])
        self.left_wheel = left_wheel

        right_wheel = Circle(
            radius=wheel_radius,
            color=color,
            stroke_width=stroke_width,
            fill_color=BLACK,
            fill_opacity=1.0
        ).shift([
            width/4,
            -wheel_radius,
            0
        ])
        self.right_wheel = right_wheel

        left_axle = Dot(
            point=left_wheel.get_center(),
            radius=0.05,
            color=color
        )
        self.left_axle = left_axle

        right_axle = Dot(
            point=right_wheel.get_center(),
            radius=0.05,
            color=color
        )
        self.right_axle = right_axle

        self.add(body, left_wheel, right_wheel, left_axle, right_axle)
        self._init_anchors(width=width, height=height, wheel_radius=wheel_radius)

    def _init_anchors(self, width: float, height: float, wheel_radius: float) -> None:
        half_w = width / 2.0
        half_h = height / 2.0
        axle_y = -wheel_radius
        left_axle_x = -width / 4.0
        right_axle_x = width / 4.0
        wheel_contact_y = axle_y - wheel_radius

        local_points = {
            "center": np.array([0.0, 0.0, 0.0]),
            "top_center": np.array([0.0, height, 0.0]),
            "left_center": np.array([-half_w, half_h, 0.0]),
            "right_center": np.array([half_w, half_h, 0.0]),
            "top_left": np.array([-half_w, height, 0.0]),
            "top_right": np.array([half_w, height, 0.0]),
            "bottom_left": np.array([-half_w, 0.0, 0.0]),
            "bottom_right": np.array([half_w, 0.0, 0.0]),
            "axle_left": np.array([left_axle_x, axle_y, 0.0]),
            "axle_right": np.array([right_axle_x, axle_y, 0.0]),
            "wheel_left_contact": np.array([left_axle_x, wheel_contact_y, 0.0]),
            "wheel_right_contact": np.array([right_axle_x, wheel_contact_y, 0.0]),
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
