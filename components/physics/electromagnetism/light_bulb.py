"""
电磁学组件库 - Electromagnetism Components

包含专业的电磁学元件：电源、电感线圈等
所有组件都遵循教科书风格，继承自 VGroup
"""

from __future__ import annotations

import numpy as np
from manim import *
from typing import Optional, Union

class LightBulb(VGroup):
    """??????"""

    def __init__(
        self,
        radius: float = 0.5,
        wire_length: float = 0.5,
        stroke_width: float = 4.0,
        color: str = WHITE,
        **kwargs
    ):
        super().__init__(**kwargs)

        left_wire = Line(
            start=[-radius - wire_length, 0, 0],
            end=[0, 0, 0],
            color=color,
            stroke_width=stroke_width
        )

        right_wire = Line(
            start=[0, 0, 0],
            end=[radius + wire_length, 0, 0],
            color=color,
            stroke_width=stroke_width
        )

        body = Circle(
            radius=radius,
            stroke_color=color,
            stroke_width=stroke_width,
            fill_color=BLACK,
            fill_opacity=1.0
        )
        body.move_to(ORIGIN)

        cross_length = radius * 2 * 0.7

        cross1 = Line(
            start=[-cross_length/2, 0, 0],
            end=[cross_length/2, 0, 0],
            color=color,
            stroke_width=stroke_width
        )
        cross1.rotate(45 * DEGREES, about_point=ORIGIN)

        cross2 = Line(
            start=[-cross_length/2, 0, 0],
            end=[cross_length/2, 0, 0],
            color=color,
            stroke_width=stroke_width
        )
        cross2.rotate(-45 * DEGREES, about_point=ORIGIN)

        cross = VGroup(cross1, cross2)
        cross.move_to(ORIGIN)

        self.add(left_wire)
        self.add(right_wire)
        self.add(body)
        self.add(cross)

        left_wire.set_z_index(0)
        right_wire.set_z_index(0)
        body.set_z_index(1)
        cross.set_z_index(2)

        self.left_wire = left_wire
        self.right_wire = right_wire
        self.body = body
        self.cross = cross
        self.radius = radius
        self.wire_length = wire_length

    def get_left_terminal(self) -> np.ndarray:
        return self.left_wire.get_start()

    def get_right_terminal(self) -> np.ndarray:
        return self.right_wire.get_end()
