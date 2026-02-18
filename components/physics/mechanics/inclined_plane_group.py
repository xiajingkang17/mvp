from __future__ import annotations

import math
import numpy as np
from manim import *
from typing import Optional, List, Tuple

class InclinedPlaneGroup(VGroup):
    """斜面滑块受力分析组合组件。"""

    def __init__(
        self,
        angle: float = 30,
        length: float = 5.0,
        block_width: float = 1.0,
        block_height: float = 0.6,
        show_forces: bool = True,
        show_angle: bool = True,
        **kwargs
    ):
        super().__init__(**kwargs)

        angle_rad = angle * DEGREES

        triangle_height = length * math.tan(angle_rad)

        inclined_plane = Polygon(
            [length/2, 0, 0],
            [-length/2, 0, 0],
            [-length/2, triangle_height, 0],
            color=BLUE_B,
            fill_opacity=0.3,
            stroke_width=3
        )
        self.inclined_plane = inclined_plane

        block = Rectangle(
            width=block_width,
            height=block_height,
            color=ORANGE,
            fill_opacity=0.8,
            stroke_width=2
        )

        slope_center_x = 0
        slope_center_y = triangle_height / 2

        block.rotate(angle_rad, about_point=ORIGIN)

        block_position = self._calculate_block_position(
            angle, length, triangle_height, block_width, block_height
        )
        block.move_to(block_position)

        self.block = block

        if show_angle:
            angle_arc = self._create_angle_arc(angle, length)
            angle_label = MathTex(r"\theta", font_size=36).next_to(
                angle_arc,
                direction=DOWN + RIGHT,
                buff=0.1
            )
            self.angle_arc = angle_arc
            self.angle_label = angle_label
        else:
            self.angle_arc = None
            self.angle_label = None

        if show_forces:
            block_center = block.get_center()

            gravity_vector = self._create_force_vector(
                start_point=block_center,
                direction=DOWN,
                length=1.5,
                color=RED,
                label=r"mg"
            )
            self.gravity = gravity_vector

            normal_direction = rotate_vector(UP, angle_rad)
            normal_vector = self._create_force_vector(
                start_point=block_center,
                direction=normal_direction,
                length=1.5,
                color=BLUE,
                label=r"F_N"
            )
            self.normal_force = normal_vector

            friction_direction = rotate_vector(LEFT, angle_rad)
            friction_vector = self._create_force_vector(
                start_point=block_center,
                direction=friction_direction,
                length=1.2,
                color=GREEN,
                label=r"f"
            )
            self.friction = friction_vector
        else:
            self.gravity = None
            self.normal_force = None
            self.friction = None

        self.add(inclined_plane)
        self.add(block)

        if show_angle:
            self.add(angle_arc)
            self.add(angle_label)

        if show_forces:
            self.add(gravity_vector)
            self.add(normal_vector)
            self.add(friction_vector)

    def _calculate_block_position(
        self,
        angle: float,
        length: float,
        triangle_height: float,
        block_width: float,
        block_height: float
    ) -> np.ndarray:
        """
        计算滑块在斜面上的位置

        Args:
            angle: 斜面角度（度）
            length: 底边长度
            triangle_height: 三角形高度
            block_width: 滑块宽度
            block_height: 滑块高度

        Returns:
            滑块中心坐标 [x, y, 0]
        """
        angle_rad = angle * DEGREES

        distance_along_slope = math.sqrt(length**2 + triangle_height**2) / 2

        start_x = -length/2
        start_y = 0

        slope_x = start_x + distance_along_slope * math.cos(angle_rad)
        slope_y = start_y + distance_along_slope * math.sin(angle_rad)

        normal_x = -math.sin(angle_rad)
        normal_y = math.cos(angle_rad)

        center_x = slope_x + (block_height / 2) * normal_x
        center_y = slope_y + (block_height / 2) * normal_y

        return np.array([center_x, center_y, 0])

    def _create_angle_arc(
        self,
        angle: float,
        length: float
    ) -> Arc:
        """
        创建角度标注弧线

        Args:
            angle: 角度值（度）
            length: 底边长度

        Returns:
            弧线对象
        """
        arc = Arc(
            radius=0.8,
            start_angle=0,
            angle=angle * DEGREES,
            color=WHITE,
            stroke_width=2
        )

        arc.shift([-length/2, 0, 0])

        return arc

    def _create_force_vector(
        self,
        start_point: np.ndarray,
        direction: np.ndarray,
        length: float = 1.5,
        color: str = YELLOW,
        label: str = ""
    ) -> VGroup:
        """
        创建力向量箭头及其标签

        Args:
            start_point: 箭头起点坐标
            direction: 方向向量
            length: 箭头长度
            color: 颜色
            label: LaTeX 标签

        Returns:
            包含箭头和标签的 VGroup
        """
        direction = direction / np.linalg.norm(direction)

        end_point = start_point + direction * length

        arrow = Arrow(
            start_point,
            end_point,
            buff=0,
            color=color,
            stroke_width=4,
            max_tip_length_to_length_ratio=0.3
        )

        result = VGroup(arrow)

        if label:
            label_tex = MathTex(label, font_size=32, color=color)
            label_position = end_point + direction * 0.3
            label_tex.move_to(label_position)

            result.add(label_tex)

        return result

    def slide_block(self, distance: float = 0.5) -> Animation:
        """
        创建滑块沿斜面滑动的动画

        Args:
            distance: 滑动距离

        Returns:
            Manim 动画对象
        """
        angle_rad = self.get_angle() * DEGREES
        direction = np.array([math.cos(angle_rad), math.sin(angle_rad), 0])

        return self.block.animate.shift(direction * distance)

    def get_angle(self) -> float:
        """获取斜面角度"""
        return 30

    def show_force_analysis(self) -> Animation:
        """
        创建依次显示各个力的动画

        Returns:
            Succession 动画序列
        """
        animations = []

        if self.gravity:
            animations.append(Create(self.gravity))
        if self.normal_force:
            animations.append(Create(self.normal_force))
        if self.friction:
            animations.append(Create(self.friction))

        if animations:
            return Succession(*animations)
        else:
            return Wait(0)


