"""
电磁学组件库 - Electromagnetism Components

包含专业的电磁学元件：电源、电感线圈等
所有组件都遵循教科书风格，继承自 VGroup
"""

from __future__ import annotations

import numpy as np
from manim import *
from typing import Optional, Union

class Capacitor(VGroup):
    """??????"""

    def __init__(
        self,
        height: float = 0.8,
        plate_spacing: float = 0.3,
        wire_length: float = 0.5,
        color: str = WHITE,
        stroke_width: float = 4.0,
        **kwargs
    ):
        super().__init__(**kwargs)

        total_width = 2 * wire_length + plate_spacing

        mask_height = height * 1.5
        background_mask = Rectangle(
            width=total_width,
            height=mask_height,
            stroke_color=BLACK,
            stroke_width=0,
            fill_color=BLACK,
            fill_opacity=1.0
        )
        background_mask.move_to(ORIGIN)
        background_mask.z_index = -10

        left_wire = Line(
            start=[-wire_length - plate_spacing/2, 0, 0],
            end=[-plate_spacing/2, 0, 0],
            color=color,
            stroke_width=stroke_width
        )
        left_wire.z_index = 0

        right_wire = Line(
            start=[plate_spacing/2, 0, 0],
            end=[wire_length + plate_spacing/2, 0, 0],
            color=color,
            stroke_width=stroke_width
        )
        right_wire.z_index = 0

        left_plate = Line(
            start=[-plate_spacing/2, -height/2, 0],
            end=[-plate_spacing/2, height/2, 0],
            color=color,
            stroke_width=stroke_width
        )
        left_plate.z_index = 10

        right_plate = Line(
            start=[plate_spacing/2, -height/2, 0],
            end=[plate_spacing/2, height/2, 0],
            color=color,
            stroke_width=stroke_width
        )
        right_plate.z_index = 10

        self.add(background_mask)
        self.add(left_wire)
        self.add(right_wire)
        self.add(left_plate)
        self.add(right_plate)

        self.background_mask = background_mask
        self.left_wire = left_wire
        self.right_wire = right_wire
        self.left_plate = left_plate
        self.right_plate = right_plate
        self.height = height
        self.plate_spacing = plate_spacing
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
