from __future__ import annotations

from manim import *


class Cart(VGroup):
    """小车组件。"""

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
