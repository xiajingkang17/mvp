"""
电磁学组件库 - Electromagnetism Components

包含专业的电磁学元件：电源、电感线圈等
所有组件都遵循教科书风格，继承自 VGroup
"""

from __future__ import annotations

import numpy as np
from manim import *
from typing import Optional, Union

class LED(VGroup):
    """????????"""

    def __init__(
        self,
        side_length: float = 1.2,
        wire_length: float = 0.8,
        arrow_size: float = 0.6,
        arrow_offset: tuple = (0.25, 0.15),
        color: str = WHITE,
        stroke_width: float = 4.0,
        **kwargs
    ):
        super().__init__(**kwargs)

        height = side_length * np.sqrt(3) / 2

        left_top = np.array([-side_length/2, height/2, 0])
        left_bottom = np.array([-side_length/2, -height/2, 0])
        right_tip = np.array([side_length/2, 0, 0])

        triangle = Polygon(
            left_top,
            left_bottom,
            right_tip,
            stroke_color=color,
            stroke_width=stroke_width,
            fill_color=BLACK,
            fill_opacity=1.0
        )
        triangle.z_index = 0

        bar_height = height * 1.1
        vertical_bar = Line(
            start=[side_length/2, -bar_height/2, 0],
            end=[side_length/2, bar_height/2, 0],
            color=color,
            stroke_width=stroke_width
        )
        vertical_bar.z_index = 0

        arrow_angle = 135 * DEGREES

        arrow1_center = np.array([
            -0.1,
            height/2 + 0.3,
            0
        ])

        arrow1 = Arrow(
            start=arrow1_center - LEFT * arrow_size/2,
            end=arrow1_center + LEFT * arrow_size/2,
            buff=0,
            stroke_width=stroke_width * 0.8,
            color=color,
            max_tip_length_to_length_ratio=0.25
        )

        arrow1.rotate(arrow_angle - PI, about_point=arrow1_center)

        arrow2 = arrow1.copy()
        arrow2.shift(RIGHT * arrow_offset[0] + UP * arrow_offset[1])

        arrows = VGroup(arrow1, arrow2)
        arrows.z_index = 10

        left_wire = Line(
            start=[-side_length/2 - wire_length, 0, 0],
            end=[-side_length/2, 0, 0],
            color=color,
            stroke_width=stroke_width
        )
        left_wire.z_index = 0

        right_wire = Line(
            start=[side_length/2, 0, 0],
            end=[side_length/2 + wire_length, 0, 0],
            color=color,
            stroke_width=stroke_width
        )
        right_wire.z_index = 0

        self.add(triangle)
        self.add(vertical_bar)
        self.add(arrows)
        self.add(left_wire)
        self.add(right_wire)

        triangle.set_z_index(0)
        vertical_bar.set_z_index(0)
        arrows.set_z_index(10)
        left_wire.set_z_index(0)
        right_wire.set_z_index(0)

        self.triangle = triangle
        self.vertical_bar = vertical_bar
        self.arrows = arrows
        self.arrow1 = arrow1
        self.arrow2 = arrow2
        self.left_wire = left_wire
        self.right_wire = right_wire
        self.side_length = side_length
        self.height = height
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
