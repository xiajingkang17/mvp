from __future__ import annotations

import math
import numpy as np
from manim import *
from typing import Dict, List, Optional, Tuple

class QuarterCart(VGroup):
    """四分之一圆小车组件，内置语义锚点。"""

    def __init__(
        self,
        side_length: float = 2.0,
        wheel_radius: float = 0.25,
        color: str = WHITE,
        stroke_width: float = 4.0,
        **kwargs
    ):
        super().__init__(**kwargs)
        self._anchor_points: Dict[str, VectorizedPoint] = {}

        base_square = Square(
            side_length=side_length,
            color=color,
            stroke_width=stroke_width,
            fill_color=BLACK,
            fill_opacity=1.0
        )

        groove_radius = side_length * 0.9
        cutter_circle = Circle(
            radius=groove_radius,
            color=color,
            stroke_width=stroke_width,
            fill_color=BLACK,
            fill_opacity=1.0
        )

        cutter_circle.move_to(base_square.get_corner(UR))

        cart_body = Difference(base_square, cutter_circle)
        cart_body.set_style(
            stroke_color=color,
            stroke_width=stroke_width,
            fill_color=BLACK,
            fill_opacity=1.0
        )
        self.cart_body = cart_body

        left_wheel = Circle(
            radius=wheel_radius,
            color=color,
            stroke_width=stroke_width,
            fill_color=BLACK,
            fill_opacity=1.0
        )
        self.left_wheel = left_wheel

        right_wheel = Circle(
            radius=wheel_radius,
            color=color,
            stroke_width=stroke_width,
            fill_color=BLACK,
            fill_opacity=1.0
        )
        self.right_wheel = right_wheel

        wheel_y = cart_body.get_bottom()[1] - wheel_radius
        wheel_x_offset = side_length * 0.25

        left_wheel.move_to(ORIGIN).shift(LEFT * wheel_x_offset + UP * wheel_y)
        right_wheel.move_to(ORIGIN).shift(RIGHT * wheel_x_offset + UP * wheel_y)

        self.add(cart_body, left_wheel, right_wheel)
        self._init_anchors(side_length=side_length, groove_radius=groove_radius, wheel_radius=wheel_radius)
        self.move_to(ORIGIN)

    def _init_anchors(self, side_length: float, groove_radius: float, wheel_radius: float) -> None:
        half = side_length / 2.0
        arc_center = np.array([half, half, 0.0])
        arc_mid = arc_center + np.array(
            [-groove_radius / math.sqrt(2.0), -groove_radius / math.sqrt(2.0), 0.0]
        )

        wheel_x_offset = side_length * 0.25
        wheel_y = -half - wheel_radius
        axle = np.array([0.0, wheel_y, 0.0])
        wheel_contact = np.array([0.0, wheel_y - wheel_radius, 0.0])

        corner = np.array([-half, -half, 0.0])
        local_points = {
            "center": arc_center,
            "corner": corner,
            "end_x": np.array([half, -half, 0.0]),
            "end_y": np.array([-half, half, 0.0]),
            "arc_mid": arc_mid,
            "axle": axle,
            "wheel_contact": wheel_contact,
            "support_corner": corner,
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
