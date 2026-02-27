from __future__ import annotations

import math
import numpy as np
from manim import *
from typing import Dict, List, Optional, Tuple

class SemicircleCart(VGroup):
    """半圆小车组件，内置语义锚点。"""

    def __init__(
        self,
        height: float = 2.0,
        wheel_radius: float = 0.25,
        color: str = WHITE,
        stroke_width: float = 4.0,
        **kwargs
    ):
        super().__init__(**kwargs)
        self._anchor_points: Dict[str, VectorizedPoint] = {}

        body_height = height
        body_width = body_height * 2.0
        groove_radius = body_height * 0.9

        base_rect = Rectangle(
            width=body_width,
            height=body_height,
            color=color,
            stroke_width=stroke_width,
            fill_color=BLACK,
            fill_opacity=1.0
        )

        cutter_circle = Circle(
            radius=groove_radius,
            color=color,
            stroke_width=stroke_width,
            fill_color=BLACK,
            fill_opacity=1.0
        )

        cutter_circle.move_to(base_rect.get_top())

        cart_body = Difference(base_rect, cutter_circle)
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
        wheel_x_offset = body_width * 0.25

        left_wheel.move_to(ORIGIN).shift(LEFT * wheel_x_offset + UP * wheel_y)
        right_wheel.move_to(ORIGIN).shift(RIGHT * wheel_x_offset + UP * wheel_y)

        self.add(cart_body, left_wheel, right_wheel)
        self._init_anchors(body_width=body_width, body_height=body_height, groove_radius=groove_radius, wheel_radius=wheel_radius)
        self.move_to(ORIGIN)

    def _init_anchors(
        self,
        body_width: float,
        body_height: float,
        groove_radius: float,
        wheel_radius: float,
    ) -> None:
        half_w = body_width / 2.0
        half_h = body_height / 2.0
        arc_center = np.array([0.0, half_h, 0.0])
        wheel_x_offset = body_width * 0.25
        axle_y = -half_h - wheel_radius
        contact_y = axle_y - wheel_radius

        local_points = {
            "center": arc_center,
            "left_end": np.array([-half_w, half_h, 0.0]),
            "right_end": np.array([half_w, half_h, 0.0]),
            "top": np.array([0.0, half_h + groove_radius, 0.0]),
            "arc_mid": np.array([0.0, half_h + groove_radius, 0.0]),
            "base_mid": np.array([0.0, -half_h, 0.0]),
            "axle_left": np.array([-wheel_x_offset, axle_y, 0.0]),
            "axle_right": np.array([wheel_x_offset, axle_y, 0.0]),
            "wheel_left_contact": np.array([-wheel_x_offset, contact_y, 0.0]),
            "wheel_right_contact": np.array([wheel_x_offset, contact_y, 0.0]),
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
