"""
电磁学组件库 - Electromagnetism Components

包含专业的电磁学元件：电源、电感线圈等
所有组件都遵循教科书风格，继承自 VGroup
"""

from __future__ import annotations

import numpy as np
from manim import *
from typing import Optional, Union

class Rheostat(VGroup):
    """????????"""

    def __init__(
        self,
        body_width: float = 2.0,
        body_height: float = 0.5,
        handle_height: float = 0.8,
        alpha: float = 0.5,
        wire_length: float = 0.5,
        terminal_radius: float = 0.08,
        color: str = WHITE,
        stroke_width: float = 4.0,
        **kwargs
    ):
        super().__init__(**kwargs)

        body_left = -body_width / 2
        body_right = body_width / 2
        body_top = body_height / 2
        body_bottom = -body_height / 2

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
            start=[body_left - wire_length, 0, 0],
            end=[body_left, 0, 0],
            color=color,
            stroke_width=stroke_width
        )
        left_wire.z_index = 0

        right_wire = Line(
            start=[body_right, 0, 0],
            end=[body_right + wire_length, 0, 0],
            color=color,
            stroke_width=stroke_width
        )
        right_wire.z_index = 0

        terminal_a = Circle(
            radius=terminal_radius,
            color=color,
            stroke_width=stroke_width * 0.5,
            fill_color=BLACK,
            fill_opacity=1.0
        )
        terminal_a.move_to([body_left - wire_length, 0, 0])
        terminal_a.z_index = 10

        terminal_b = Circle(
            radius=terminal_radius,
            color=color,
            stroke_width=stroke_width * 0.5,
            fill_color=BLACK,
            fill_opacity=1.0
        )
        terminal_b.move_to([body_right + wire_length, 0, 0])
        terminal_b.z_index = 10

        alpha = max(0.0, min(1.0, alpha))
        contact_x = body_left + alpha * body_width
        contact_point = np.array([contact_x, body_top, 0])

        vertical_top = np.array([contact_x, body_top + handle_height, 0])

        terminal_c_pos = np.array([body_right, body_top + handle_height, 0])

        vertical_wire = Line(
            start=contact_point,
            end=vertical_top,
            color=color,
            stroke_width=stroke_width
        )
        vertical_wire.z_index = 10

        horizontal_wire = Line(
            start=vertical_top,
            end=terminal_c_pos,
            color=color,
            stroke_width=stroke_width
        )
        horizontal_wire.z_index = 10

        arrow_size = 0.12
        arrow_height = arrow_size * 1.5

        arrow = Polygon(
            [contact_point[0] - arrow_size, contact_point[1] + arrow_height, 0],
            [contact_point[0] + arrow_size, contact_point[1] + arrow_height, 0],
            [contact_point[0], contact_point[1], 0],
            color=color,
            stroke_width=stroke_width * 0.8
        )
        arrow.set_fill(BLACK, opacity=1.0)
        arrow.z_index = 10

        terminal_c = Circle(
            radius=terminal_radius,
            color=color,
            stroke_width=stroke_width * 0.5,
            fill_color=BLACK,
            fill_opacity=1.0
        )
        terminal_c.move_to(terminal_c_pos)
        terminal_c.z_index = 10

        self.add(body)
        self.add(left_wire, right_wire)
        self.add(terminal_a, terminal_b, terminal_c)
        self.add(vertical_wire, horizontal_wire)
        self.add(arrow)

        self.body = body
        self.left_wire = left_wire
        self.right_wire = right_wire
        self.terminal_a = terminal_a
        self.terminal_b = terminal_b
        self.terminal_c = terminal_c
        self.vertical_wire = vertical_wire
        self.horizontal_wire = horizontal_wire
        self.arrow = arrow
        self.body_width = body_width
        self.body_height = body_height
        self.handle_height = handle_height
        self.wire_length = wire_length
        self.alpha = alpha
        self.terminal_radius = terminal_radius

    def get_terminal_a(self) -> np.ndarray:
        """
        获取左端接线柱 (A) 中心坐标

        Returns:
            接线柱 A 的三维坐标 [x, y, z]
        """
        return self.terminal_a.get_center()

    def get_terminal_b(self) -> np.ndarray:
        """
        获取右端接线柱 (B) 中心坐标

        Returns:
            接线柱 B 的三维坐标 [x, y, z]
        """
        return self.terminal_b.get_center()

    def get_terminal_c(self) -> np.ndarray:
        """
        获取滑动端接线柱 (C) 中心坐标

        Returns:
            接线柱 C 的三维坐标 [x, y, z]
        """
        return self.terminal_c.get_center()

    def change_value(self, new_alpha: float):
        """
        更新滑片位置

        参数:
            new_alpha: 新的滑片位置，范围 [0.0, 1.0]
        """
        new_alpha = max(0.0, min(1.0, new_alpha))
        self.alpha = new_alpha

        body_left = -self.body_width / 2
        body_top = self.body_height / 2
        contact_x = body_left + new_alpha * self.body_width
        contact_point = np.array([contact_x, body_top, 0])
        vertical_top = np.array([contact_x, body_top + self.handle_height, 0])
        terminal_c_pos = np.array([self.body_width / 2, body_top + self.handle_height, 0])

        self.vertical_wire.put_start_and_end_on(contact_point, vertical_top)

        self.horizontal_wire.put_start_and_end_on(vertical_top, terminal_c_pos)

        arrow_size = 0.12
        arrow_height = arrow_size * 1.5
        self.arrow.set_points_as_corners([
            [contact_x - arrow_size, body_top + arrow_height, 0],
            [contact_x + arrow_size, body_top + arrow_height, 0],
            [contact_x, body_top, 0]
        ])

        self.terminal_c.move_to(terminal_c_pos)
