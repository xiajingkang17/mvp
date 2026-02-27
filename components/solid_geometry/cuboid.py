"""
长方体组件 - Cuboid Geometry (斜二测画法)

实现中国高中教材风格的斜二测长方体可视化。

核心架构（2026-02-19）:
- 采用"绝对中心构建法"（Absolute Center Method）
- 基于正方体组件扩展，支持不同的长宽高
- 标准 45° 斜二测画法
- 缩短系数 0.5（可配置）

作者: Manim 数学组件库
日期: 2026-02-19
"""

from __future__ import annotations

import numpy as np
from manim import *
from typing import Dict, Tuple, Optional


class CuboidOblique(VGroup):
    """
    斜二测长方体组件（纯 2D 投影）

    特性：
    - 标准 45° 斜二测画法
    - 缩短系数 0.5（可配置）
    - 支持不同的长宽高
    - 手动虚实线控制
    - 手动标签布局（避免遮挡）

    参数：
    -------
    length : float
        长度（x 轴方向，默认 2.0）
    width : float
        宽度（y 轴方向，默认 1.5）
    height : float
        高度（z 轴方向，默认 2.5）
    shortening_factor : float
        斜二测缩短系数（默认 0.5）
    angle : float
        倾斜角度（弧度，默认 PI/4 = 45°）
    show_axes : bool
        是否显示坐标轴（默认 True）
    show_labels : bool
        是否显示顶点标签（默认 True）
    center : np.ndarray
        底面中心的绝对坐标（默认 ORIGIN）
    **kwargs
        其他 VGroup 参数
    """

    def __init__(
        self,
        length: float = 2.0,
        width: float = 1.5,
        height: float = 2.5,
        shortening_factor: float = 0.5,
        angle: float = PI / 4,
        show_axes: bool = True,
        show_labels: bool = True,
        center: np.ndarray = ORIGIN,
        **kwargs
    ):
        super().__init__(**kwargs)

        # 保存参数
        self.length = length
        self.width = width
        self.height = height
        self.shortening_factor = shortening_factor
        self.angle = angle
        self.show_axes = show_axes
        self.show_labels = show_labels

        # ========== 步骤 A: 锁定关键点（Key Points）- 定海神针 ==========
        # 底面中心
        self.p_center = center

        # 计算斜轴方向向量
        self.x_axis = RIGHT  # 水平向右
        self.y_axis = rotate_vector(RIGHT, -angle) * shortening_factor  # 斜向左下
        self.z_axis = UP  # 竖直向上

        # 底面四个顶点（相对于中心）
        self.p_bottom_front_left = self.p_center - self.x_axis * (length / 2) - self.y_axis * (width / 2)
        self.p_bottom_front_right = self.p_center + self.x_axis * (length / 2) - self.y_axis * (width / 2)
        self.p_bottom_back_left = self.p_center - self.x_axis * (length / 2)
        self.p_bottom_back_right = self.p_center + self.x_axis * (length / 2)

        # 顶面四个顶点
        self.p_top_front_left = self.p_bottom_front_left + self.z_axis * height
        self.p_top_front_right = self.p_bottom_front_right + self.z_axis * height
        self.p_top_back_left = self.p_bottom_back_left + self.z_axis * height
        self.p_top_back_right = self.p_bottom_back_right + self.z_axis * height

        # ========== 步骤 B: 绘制底面（实线）==========
        self.bottom_face = VGroup(
            Line(self.p_bottom_front_left, self.p_bottom_front_right, color=WHITE),
            Line(self.p_bottom_front_right, self.p_bottom_back_right, color=WHITE),
            Line(self.p_bottom_back_right, self.p_bottom_back_left, color=WHITE),
            Line(self.p_bottom_back_left, self.p_bottom_front_left, color=WHITE),
        )

        # ========== 步骤 C: 绘制虚线边（不可见的棱）==========
        self.hidden_edges = VGroup(
            Line(self.p_bottom_front_left, self.p_top_front_left, color=GRAY),
            Line(self.p_bottom_front_left, self.p_bottom_back_left, color=GRAY),
        )
        self.hidden_edges = DashedVMobject(self.hidden_edges, dashed_ratio=0.5)

        # ========== 步骤 D: 绘制可见棱（实线）==========
        self.visible_edges = VGroup(
            Line(self.p_bottom_front_right, self.p_top_front_right, color=WHITE),
            Line(self.p_bottom_back_right, self.p_top_back_right, color=WHITE),
            Line(self.p_bottom_back_left, self.p_top_back_left, color=GRAY),
            Line(self.p_top_front_left, self.p_top_front_right, color=WHITE),
            Line(self.p_top_front_right, self.p_top_back_right, color=WHITE),
            Line(self.p_top_back_right, self.p_top_back_left, color=WHITE),
        )

        # ========== 步骤 E: 绘制坐标轴 ==========
        if show_axes:
            self._create_axes()

        # ========== 步骤 F: 创建标签 ==========
        if show_labels:
            self._create_labels()

        # ========== 组装组件（层级处理）==========
        self.add(self.hidden_edges)  # 虚线（最底层）
        self.add(self.bottom_face)
        self.add(self.visible_edges)

        if show_axes:
            self.add(self.inner_axes)
            self.add(self.outer_axes)

        if show_labels:
            self.add(self.labels)

    def _create_axes(self):
        """创建坐标轴"""
        self.inner_axes = VGroup()
        self.outer_axes = VGroup()

        # X 轴（水平向右，GREEN）
        x_inner = DashedLine(
            start=self.p_center,
            end=self.p_center + self.x_axis * (length / 2),
            color=GREEN_B,
            stroke_width=3,
            dash_length=0.15,
            stroke_opacity=0.7
        )
        self.inner_axes.add(x_inner)

        x_outer = Arrow(
            start=self.p_center + self.x_axis * (length / 2),
            end=self.p_center + self.x_axis * (length / 2 + 1.5),
            color=GREEN_B,
            stroke_width=4,
            max_tip_length_to_length_ratio=0.15,
            buff=0
        )
        x_label = MathTex("x", font_size=24, color=GREEN_B)
        x_label.move_to(x_outer.get_end() + RIGHT * 0.3)
        self.outer_axes.add(x_outer, x_label)

        # Y 轴（斜向左下，RED）
        y_inner = DashedLine(
            start=self.p_center,
            end=self.p_center + self.y_axis * (width / 2),
            color=RED_B,
            stroke_width=3,
            dash_length=0.15,
            stroke_opacity=0.7
        )
        self.inner_axes.add(y_inner)

        y_outer = Arrow(
            start=self.p_center + self.y_axis * (width / 2),
            end=self.p_center + self.y_axis * (width / 2 + 1.5),
            color=RED_B,
            stroke_width=4,
            max_tip_length_to_length_ratio=0.15,
            buff=0
        )
        y_label = MathTex("y", font_size=24, color=RED_B)
        y_label.move_to(y_outer.get_end() + self.y_axis * 0.5)
        self.outer_axes.add(y_outer, y_label)

        # Z 轴（竖直向上，BLUE）
        z_inner = DashedLine(
            start=self.p_center,
            end=self.p_center + self.z_axis * (height / 2),
            color=BLUE_B,
            stroke_width=3,
            dash_length=0.15,
            stroke_opacity=0.7
        )
        self.inner_axes.add(z_inner)

        z_outer = Arrow(
            start=self.p_center + self.z_axis * (height / 2),
            end=self.p_center + self.z_axis * (height / 2 + 1.0),
            color=BLUE_B,
            stroke_width=4,
            max_tip_length_to_length_ratio=0.15,
            buff=0
        )
        z_label = MathTex("z", font_size=24, color=BLUE_B)
        z_label.move_to(z_outer.get_end() + UP * 0.3)
        self.outer_axes.add(z_outer, z_label)

    def _create_labels(self):
        """创建顶点标签"""
        self.labels = VGroup()

        # 底面顶点
        labels = [
            ("A", self.p_bottom_front_left, DOWN + LEFT),
            ("B", self.p_bottom_front_right, DOWN + RIGHT),
            ("C", self.p_bottom_back_right, DOWN + RIGHT),
            ("D", self.p_bottom_back_left, DOWN + LEFT),
        ]

        # 顶面顶点
        labels.extend([
            ("A'", self.p_top_front_left, UP + LEFT),
            ("B'", self.p_top_front_right, UP + RIGHT),
            ("C'", self.p_top_back_right, UP + RIGHT),
            ("D'", self.p_top_back_left, UP + LEFT),
        ])

        for name, point, direction in labels:
            label = MathTex(name, font_size=20, color=YELLOW)
            label.move_to(point + direction * 0.5)
            self.labels.add(label)

    def get_key_points(self) -> dict:
        """
        获取所有关键点（用于调试和验证）

        Returns:
            dict: 包含所有关键点的字典
        """
        return {
            "p_center": self.p_center,
            "p_bottom_front_left": self.p_bottom_front_left,
            "p_bottom_front_right": self.p_bottom_front_right,
            "p_bottom_back_left": self.p_bottom_back_left,
            "p_bottom_back_right": self.p_bottom_back_right,
            "p_top_front_left": self.p_top_front_left,
            "p_top_front_right": self.p_top_front_right,
            "p_top_back_left": self.p_top_back_left,
            "p_top_back_right": self.p_top_back_right,
        }
