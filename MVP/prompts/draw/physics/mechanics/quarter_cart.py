from __future__ import annotations

from manim import *


class QuarterCart(VGroup):
    """四分之一圆小车组件。"""

    def __init__(
        self,
        side_length: float = 2.0,
        wheel_radius: float = 0.25,
        color: str = WHITE,
        stroke_width: float = 4.0,
        **kwargs
    ):
        super().__init__(**kwargs)

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
        self.move_to(ORIGIN)
