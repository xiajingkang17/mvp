"""
电磁学组件库 - Electromagnetism Components

包含专业的电磁学元件：电源、电感线圈等
所有组件都遵循教科书风格，继承自 VGroup
"""

from __future__ import annotations

import numpy as np
from manim import *
from typing import Optional, Union

class Inductor(VGroup):
    """???????"""

    def __init__(
        self,
        num_loops: int = 4,
        radius: float = 0.2,
        wire_length: float = 0.5,
        color: str = WHITE,
        stroke_width: float = 4.0,
        **kwargs
    ):
        super().__init__(**kwargs)

        coil_width = num_loops * 2 * radius
        coil_height = radius * 2

        coils = VGroup()

        for i in range(num_loops):
            arc = Arc(
                radius=radius,
                start_angle=PI,
                angle=-PI,
                color=color,
                stroke_width=stroke_width
            )

            arc.shift(RIGHT * (i * 2 * radius))
            coils.add(arc)

        coils.move_to(ORIGIN)

        background_mask = Rectangle(
            width=coil_width,
            height=coil_height,
            stroke_color=BLACK,
            stroke_width=0,
            fill_color=BLACK,
            fill_opacity=1.0
        )
        background_mask.move_to(ORIGIN)
        background_mask.z_index = -10

        coil_left_x = -coil_width / 2
        coil_right_x = coil_width / 2

        left_wire = Line(
            start=[coil_left_x - wire_length, 0, 0],
            end=[coil_left_x, 0, 0],
            color=color,
            stroke_width=stroke_width
        )
        left_wire.z_index = 0

        right_wire = Line(
            start=[coil_right_x, 0, 0],
            end=[coil_right_x + wire_length, 0, 0],
            color=color,
            stroke_width=stroke_width
        )
        right_wire.z_index = 0

        coils.set_z_index(0)

        self.add(background_mask)
        self.add(left_wire)
        self.add(right_wire)
        self.add(coils)

        background_mask.set_z_index(-10)
        left_wire.set_z_index(0)
        right_wire.set_z_index(0)
        coils.set_z_index(0)

        self.background_mask = background_mask
        self.left_wire = left_wire
        self.right_wire = right_wire
        self.coils = coils
        self.num_loops = num_loops
        self.radius = radius
        self.coil_width = coil_width
        self.coil_height = coil_height
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
