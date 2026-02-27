"""
电磁学组件库 - Electromagnetism Components

包含专业的电磁学元件：电源、电感线圈等
所有组件都遵循教科书风格，继承自 VGroup
"""

from __future__ import annotations

import numpy as np
from manim import *
from typing import Optional, Union

class Ammeter(VGroup):
    """??????"""

    def __init__(
        self,
        radius: float = 0.4,
        wire_length: float = 0.5,
        label_scale: float = 0.7,
        color: str = WHITE,
        stroke_width: float = 4.0,
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

        circle = Circle(
            radius=radius,
            stroke_color=color,
            stroke_width=stroke_width,
            fill_color=BLACK,
            fill_opacity=1.0
        )
        circle.move_to(ORIGIN)

        label = Text(
            "A",
            font_size=48,
            color=WHITE,
            fill_opacity=1.0,
            stroke_width=0
        )
        label.move_to(ORIGIN)
        label.scale(label_scale)

        self.add(left_wire)
        self.add(right_wire)
        self.add(circle)

        self.add(label)

        left_wire.set_z_index(0)
        right_wire.set_z_index(0)
        circle.set_z_index(1)
        label.set_z_index(2)

        self.left_wire = left_wire
        self.right_wire = right_wire
        self.circle = circle
        self.label = label
        self.radius = radius
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
