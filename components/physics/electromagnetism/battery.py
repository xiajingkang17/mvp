"""
电磁学组件库 - Electromagnetism Components

包含专业的电磁学元件：电源、电感线圈等
所有组件都遵循教科书风格，继承自 VGroup
"""

from __future__ import annotations

import numpy as np
from manim import *
from typing import Optional, Union

class Battery(VGroup):
    """???????"""

    def __init__(
        self,
        height: float = 0.8,
        ratio: float = 0.55,
        plate_spacing: float = 0.3,
        wire_length: float = 0.5,
        is_positive_left: bool = True,
        color: str = WHITE,
        stroke_width: float = 4.0,
        **kwargs
    ):
        super().__init__(**kwargs)

        positive_height = height
        negative_height = height * ratio

        total_width = 2 * wire_length + plate_spacing

        mask_height = positive_height * 1.5
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

        positive_plate = Line(
            start=[0, -positive_height/2, 0],
            end=[0, positive_height/2, 0],
            color=color,
            stroke_width=stroke_width
        )

        negative_plate = Line(
            start=[0, -negative_height/2, 0],
            end=[0, negative_height/2, 0],
            color=color,
            stroke_width=stroke_width * 1.2
        )

        left_wire = Line(
            start=[-wire_length, 0, 0],
            end=[0, 0, 0],
            color=color,
            stroke_width=stroke_width
        )

        right_wire = Line(
            start=[0, 0, 0],
            end=[wire_length, 0, 0],
            color=color,
            stroke_width=stroke_width
        )

        if is_positive_left:
            positive_plate.shift(LEFT * plate_spacing / 2)
            negative_plate.shift(RIGHT * plate_spacing / 2)

            left_wire_end = positive_plate.get_center()[0]
            left_wire.put_start_and_end_on(
                [-wire_length, 0, 0],
                [left_wire_end, 0, 0]
            )

            right_wire_start = negative_plate.get_center()[0]
            right_wire.put_start_and_end_on(
                [right_wire_start, 0, 0],
                [right_wire_start + wire_length, 0, 0]
            )
        else:
            negative_plate.shift(LEFT * plate_spacing / 2)
            positive_plate.shift(RIGHT * plate_spacing / 2)

            left_wire_end = negative_plate.get_center()[0]
            left_wire.put_start_and_end_on(
                [-wire_length, 0, 0],
                [left_wire_end, 0, 0]
            )

            right_wire_start = positive_plate.get_center()[0]
            right_wire.put_start_and_end_on(
                [right_wire_start, 0, 0],
                [right_wire_start + wire_length, 0, 0]
            )


        background_mask.z_index = -10
        left_wire.z_index = 0
        right_wire.z_index = 0
        positive_plate.z_index = 10
        negative_plate.z_index = 10

        self.add(background_mask)
        self.add(left_wire, right_wire)
        self.add(positive_plate, negative_plate)

        self.background_mask = background_mask
        self.positive_plate = positive_plate
        self.negative_plate = negative_plate
        self.left_wire = left_wire
        self.right_wire = right_wire
        self.is_positive_left = is_positive_left

    def get_positive_terminal(self) -> np.ndarray:
        """
        获取正极接线端点坐标

        Returns:
            正极端点的三维坐标 [x, y, z]
        """
        if self.is_positive_left:
            return self.left_wire.get_start()
        else:
            return self.right_wire.get_end()

    def get_negative_terminal(self) -> np.ndarray:
        """
        获取负极接线端点坐标

        Returns:
            负极端点的三维坐标 [x, y, z]
        """
        if self.is_positive_left:
            return self.right_wire.get_end()
        else:
            return self.left_wire.get_start()
