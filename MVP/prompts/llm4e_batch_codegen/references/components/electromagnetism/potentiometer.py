"""
电磁学组件库 - Electromagnetism Components

包含专业的电磁学元件：电源、电感线圈等
所有组件都遵循教科书风格，继承自 VGroup
"""

from __future__ import annotations

import numpy as np
from manim import *
from typing import Optional, Union

class Potentiometer(VGroup):
    """??????"""

    def __init__(
        self,
        body_width: float = 1.2,
        body_height: float = 0.4,
        wire_length: float = 0.5,
        arrow_scale: float = 1.5,
        arrow_angle: float = 45 * DEGREES,
        color: str = WHITE,
        stroke_width: float = 4.0,
        **kwargs
    ):
        super().__init__(**kwargs)

        body = Rectangle(
            width=body_width,
            height=body_height,
            stroke_color=color,
            stroke_width=stroke_width,
            fill_color=BLACK,
            fill_opacity=1.0
        )
        body.move_to(ORIGIN)
        body.z_index = 0

        left_wire = Line(
            start=[-body_width/2 - wire_length, 0, 0],
            end=[-body_width/2, 0, 0],
            color=color,
            stroke_width=stroke_width
        )
        left_wire.z_index = 0

        right_wire = Line(
            start=[body_width/2, 0, 0],
            end=[body_width/2 + wire_length, 0, 0],
            color=color,
            stroke_width=stroke_width
        )
        right_wire.z_index = 0

        diagonal_length = np.sqrt(body_width**2 + body_height**2)
        
        arrow_length = diagonal_length * arrow_scale

        arrow = Arrow(
            start=LEFT * arrow_length / 2,
            end=RIGHT * arrow_length / 2,
            buff=0,
            stroke_width=stroke_width,
            color=color,
            max_tip_length_to_length_ratio=0.15
        )

        arrow.rotate(arrow_angle, about_point=ORIGIN)
        arrow.move_to(ORIGIN)
        arrow.z_index = 10

        self.add(left_wire)
        self.add(right_wire)
        self.add(body)
        self.add(arrow)

        left_wire.set_z_index(0)
        right_wire.set_z_index(0)
        body.set_z_index(1)
        arrow.set_z_index(2)

        self.left_wire = left_wire
        self.right_wire = right_wire
        self.body = body
        self.arrow = arrow
        self.body_width = body_width
        self.body_height = body_height
        self.wire_length = wire_length

    def get_left_terminal(self) -> np.ndarray:
        """
        获取左侧接线端点坐标

        Returns:
            左侧引线外端点的三维坐标 [x, y, z]
        """
        return self.left_wire.get_start()

    def get_right_terminal(self) -> np.ndarray:
        """
        获取右侧接线端点坐标

        Returns:
            右侧引线外端点的三维坐标 [x, y, z]
        """
        return self.right_wire.get_end()
