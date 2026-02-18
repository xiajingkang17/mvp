"""
电磁学组件库 - Electromagnetism Components

包含专业的电磁学元件：电源、电感线圈等
所有组件都遵循教科书风格，继承自 VGroup
"""

from __future__ import annotations

import numpy as np
from manim import *
from typing import Optional, Union

class Switch(VGroup):
    """?????????"""

    def __init__(
        self,
        wire_length: float = 0.5,
        switch_length: float = 0.8,
        is_closed: bool = False,
        open_angle: float = 30 * DEGREES,
        color: str = WHITE,
        stroke_width: float = 4.0,
        **kwargs
    ):
        super().__init__(**kwargs)

        left_terminal_pos = LEFT * switch_length / 2
        right_terminal_pos = RIGHT * switch_length / 2

        total_width = 2 * wire_length + switch_length

        mask_height = switch_length * 0.8
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
            start=[-wire_length - switch_length/2, 0, 0],
            end=left_terminal_pos,
            color=color,
            stroke_width=stroke_width
        )
        left_wire.z_index = 0

        right_wire = Line(
            start=right_terminal_pos,
            end=[wire_length + switch_length/2, 0, 0],
            color=color,
            stroke_width=stroke_width
        )
        right_wire.z_index = 0

        terminal_radius = 0.08

        left_terminal = Circle(
            radius=terminal_radius,
            color=color,
            stroke_width=stroke_width * 0.5,
            fill_color=BLACK,
            fill_opacity=1.0
        )
        left_terminal.move_to(left_terminal_pos)
        left_terminal.z_index = 10

        right_terminal = Circle(
            radius=terminal_radius,
            color=color,
            stroke_width=stroke_width * 0.5,
            fill_color=BLACK,
            fill_opacity=1.0
        )
        right_terminal.move_to(right_terminal_pos)
        right_terminal.z_index = 10

        blade = Line(
            start=left_terminal_pos,
            end=right_terminal_pos,
            color=color,
            stroke_width=stroke_width
        )
        blade.z_index = 10

        if not is_closed:
            blade.rotate(
                angle=open_angle,
                about_point=left_terminal_pos
            )

        self.add(background_mask)
        self.add(left_wire, right_wire)
        self.add(left_terminal, right_terminal)
        self.add(blade)

        self.background_mask = background_mask
        self.left_wire = left_wire
        self.right_wire = right_wire
        self.left_terminal = left_terminal
        self.right_terminal = right_terminal
        self.blade = blade
        self.switch_length = switch_length
        self.open_angle = open_angle
        self.is_closed = is_closed

    def get_left_terminal(self) -> np.ndarray:
        """
        获取左侧接线柱中心坐标

        Returns:
            左侧接线柱的三维坐标 [x, y, z]
        """
        return self.left_terminal.get_center()

    def get_right_terminal(self) -> np.ndarray:
        """
        获取右侧接线柱中心坐标

        Returns:
            右侧接线柱的三维坐标 [x, y, z]
        """
        return self.right_terminal.get_center()

    def get_left_wire_end(self) -> np.ndarray:
        """
        获取左侧引线的外端点坐标

        Returns:
            左侧引线外端点的三维坐标 [x, y, z]
        """
        return self.left_wire.get_start()

    def get_right_wire_end(self) -> np.ndarray:
        """
        获取右侧引线的外端点坐标

        Returns:
            右侧引线外端点的三维坐标 [x, y, z]
        """
        return self.right_wire.get_end()

    def close(self) -> Rotate:
        """
        闭合开关动画

        Returns:
            Rotate 动画对象，将刀闸从断开状态旋转到闭合状态
        """
        if self.is_closed:
            return Rotate(self.blade, 0, about_point=self.get_left_terminal())

        return Rotate(
            self.blade,
            angle=-self.open_angle,
            about_point=self.get_left_terminal()
        )

    def open(self) -> Rotate:
        """
        断开开关动画

        Returns:
            Rotate 动画对象，将刀闸从闭合状态旋转到断开状态
        """
        if not self.is_closed:
            return Rotate(self.blade, 0, about_point=self.get_left_terminal())

        return Rotate(
            self.blade,
            angle=self.open_angle,
            about_point=self.get_left_terminal()
        )

    def toggle(self) -> Rotate:
        """
        切换开关状态动画

        Returns:
            Rotate 动画对象，切换开关状态
        """
        if self.is_closed:
            return self.open()
        else:
            return self.close()
