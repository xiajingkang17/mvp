"""
棱锥组件 - Pyramid Geometry (斜二测画法)

实现中国高中教材风格的斜二测棱锥可视化。

核心架构（2026-02-19）:
- 采用"绝对中心构建法"（Absolute Center Method）
- 支持正四棱锥和正三棱锥
- 标准 45° 斜二测画法
- 缩短系数 0.5（可配置）

作者: Manim 数学组件库
日期: 2026-02-19
"""

from __future__ import annotations

import numpy as np
from manim import *
from typing import Dict, Tuple, Optional, List


class PyramidOblique(VGroup):
    """
    斜二测正四棱锥组件（纯 2D 投影）

    特性：
    - 标准 45° 斜二测画法
    - 缩短系数 0.5（可配置）
    - 底面为正方形
    - 手动虚实线控制
    - 手动标签布局（避免遮挡）

    参数：
    -------
    base_length : float
        底面边长（默认 2.0）
    height : float
        棱锥高度（默认 3.0）
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
        base_length: float = 2.0,
        height: float = 3.0,
        shortening_factor: float = 0.5,
        angle: float = PI / 4,
        show_axes: bool = True,
        show_labels: bool = True,
        center: np.ndarray = ORIGIN,
        **kwargs
    ):
        super().__init__(**kwargs)

        # 保存参数
        self.base_length = base_length
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
        half = base_length / 2
        self.p_bottom_front = self.p_center - self.y_axis * half
        self.p_bottom_right = self.p_center + self.x_axis * half
        self.p_bottom_back = self.p_center + self.y_axis * half
        self.p_bottom_left = self.p_center - self.x_axis * half

        # 顶点
        self.p_apex = self.p_center + self.z_axis * height

        # ========== 步骤 B: 绘制底面（虚线 + 实线）==========
        # 前边（实线）
        self.bottom_front = Line(self.p_bottom_front, self.p_bottom_right, color=WHITE)
        # 右边（实线）
        self.bottom_right = Line(self.p_bottom_right, self.p_bottom_back, color=WHITE)
        # 后边（虚线）
        self.bottom_back = Line(self.p_bottom_back, self.p_bottom_left, color=GRAY)
        self.bottom_back = DashedVMobject(self.bottom_back, dashed_ratio=0.5)
        # 左边（虚线）
        self.bottom_left = Line(self.p_bottom_left, self.p_bottom_front, color=GRAY)
        self.bottom_left = DashedVMobject(self.bottom_left, dashed_ratio=0.5)

        # ========== 步骤 C: 绘制侧棱（虚实分明）==========
        # 前侧棱（实线）
        self.edge_front = Line(self.p_bottom_front, self.p_apex, color=WHITE)
        # 右侧棱（实线）
        self.edge_right = Line(self.p_bottom_right, self.p_apex, color=WHITE)
        # 后侧棱（虚线）
        self.edge_back = Line(self.p_bottom_back, self.p_apex, color=GRAY)
        self.edge_back = DashedVMobject(self.edge_back, dashed_ratio=0.5)
        # 左侧棱（虚线）
        self.edge_left = Line(self.p_bottom_left, self.p_apex, color=GRAY)
        self.edge_left = DashedVMobject(self.edge_left, dashed_ratio=0.5)

        # ========== 步骤 D: 绘制坐标轴 ==========
        if show_axes:
            self._create_axes()

        # ========== 步骤 E: 创建标签 ==========
        if show_labels:
            self._create_labels()

        # ========== 组装组件（层级处理）==========
        self.add(self.bottom_back, self.bottom_left, self.edge_back, self.edge_left)  # 虚线（最底层）
        self.add(self.bottom_front, self.bottom_right)  # 底面实线
        self.add(self.edge_front, self.edge_right)  # 侧棱实线

        if show_axes:
            self.add(self.inner_axes)
            self.add(self.outer_axes)

        if show_labels:
            self.add(self.labels)

    def _create_axes(self):
        """创建坐标轴"""
        self.inner_axes = VGroup()
        self.outer_axes = VGroup()

        half = self.base_length / 2

        # X 轴（水平向右，GREEN）
        x_inner = DashedLine(
            start=self.p_center,
            end=self.p_center + self.x_axis * half,
            color=GREEN_B,
            stroke_width=3,
            dash_length=0.15,
            stroke_opacity=0.7
        )
        self.inner_axes.add(x_inner)

        x_outer = Arrow(
            start=self.p_center + self.x_axis * half,
            end=self.p_center + self.x_axis * (half + 1.5),
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
            end=self.p_center + self.y_axis * half,
            color=RED_B,
            stroke_width=3,
            dash_length=0.15,
            stroke_opacity=0.7
        )
        self.inner_axes.add(y_inner)

        y_outer = Arrow(
            start=self.p_center + self.y_axis * half,
            end=self.p_center + self.y_axis * (half + 1.5),
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
            end=self.p_center + self.z_axis * (self.height / 2),
            color=BLUE_B,
            stroke_width=3,
            dash_length=0.15,
            stroke_opacity=0.7
        )
        self.inner_axes.add(z_inner)

        z_outer = Arrow(
            start=self.p_center + self.z_axis * (self.height / 2),
            end=self.p_center + self.z_axis * (self.height / 2 + 1.0),
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
            ("A", self.p_bottom_front, DOWN + RIGHT),
            ("B", self.p_bottom_right, DOWN + RIGHT),
            ("C", self.p_bottom_back, UP + RIGHT),
            ("D", self.p_bottom_left, UP + LEFT),
        ]

        # 顶点
        labels.append(("S", self.p_apex, UP))

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
            "p_apex": self.p_apex,
            "p_bottom_front": self.p_bottom_front,
            "p_bottom_right": self.p_bottom_right,
            "p_bottom_back": self.p_bottom_back,
            "p_bottom_left": self.p_bottom_left,
        }


class TetrahedronOblique(VGroup):
    """
    斜二测正三棱锥组件（纯 2D 投影）

    特性：
    - 标准 45° 斜二测画法
    - 缩短系数 0.5（可配置）
    - 底面为正三角形
    - 手动虚实线控制

    参数：
    -------
    base_length : float
        底面边长（默认 2.0）
    height : float
        棱锥高度（默认 3.0）
    shortening_factor : float
        斜二测缩短系数（默认 0.5）
    angle : float
        倾倾角度（弧度，默认 PI/4 = 45°）
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
        base_length: float = 2.0,
        height: float = 3.0,
        shortening_factor: float = 0.5,
        angle: float = PI / 4,
        show_axes: bool = True,
        show_labels: bool = True,
        center: np.ndarray = ORIGIN,
        **kwargs
    ):
        super().__init__(**kwargs)

        # 保存参数
        self.base_length = base_length
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

        # 底面三个顶点（正三角形分布）
        # 前顶点（A）
        self.p_bottom_front = self.p_center - self.y_axis * (base_length / 2)
        # 右后顶点（B）
        self.p_bottom_right_back = self.p_center + self.x_axis * (base_length / 2) + self.y_axis * (base_length / 4)
        # 左后顶点（C）
        self.p_bottom_left_back = self.p_center - self.x_axis * (base_length / 2) + self.y_axis * (base_length / 4)

        # 顶点
        self.p_apex = self.p_center + self.z_axis * height

        # ========== 步骤 B: 绘制底面（虚实分明）==========
        # 前边（实线）
        self.bottom_front = Line(self.p_bottom_front, self.p_bottom_right_back, color=WHITE)
        # 左边（实线）
        self.bottom_left = Line(self.p_bottom_front, self.p_bottom_left_back, color=WHITE)
        # 后边（虚线）
        self.bottom_back = Line(self.p_bottom_right_back, self.p_bottom_left_back, color=GRAY)
        self.bottom_back = DashedVMobject(self.bottom_back, dashed_ratio=0.5)

        # ========== 步骤 C: 绘制侧棱（虚实分明）==========
        # 前侧棱（实线）
        self.edge_front = Line(self.p_bottom_front, self.p_apex, color=WHITE)
        # 右侧棱（虚线）
        self.edge_right = Line(self.p_bottom_right_back, self.p_apex, color=GRAY)
        self.edge_right = DashedVMobject(self.edge_right, dashed_ratio=0.5)
        # 左侧棱（虚线）
        self.edge_left = Line(self.p_bottom_left_back, self.p_apex, color=GRAY)
        self.edge_left = DashedVMobject(self.edge_left, dashed_ratio=0.5)

        # ========== 步骤 D: 绘制坐标轴 ==========
        if show_axes:
            self._create_axes()

        # ========== 步骤 E: 创建标签 ==========
        if show_labels:
            self._create_labels()

        # ========== 组装组件（层级处理）==========
        self.add(self.bottom_back, self.edge_right, self.edge_left)  # 虚线（最底层）
        self.add(self.bottom_front, self.bottom_left)  # 底面实线
        self.add(self.edge_front)  # 侧棱实线

        if show_axes:
            self.add(self.inner_axes)
            self.add(self.outer_axes)

        if show_labels:
            self.add(self.labels)

    def _create_axes(self):
        """创建坐标轴"""
        self.inner_axes = VGroup()
        self.outer_axes = VGroup()

        half = self.base_length / 2

        # X 轴（水平向右，GREEN）
        x_inner = DashedLine(
            start=self.p_center,
            end=self.p_center + self.x_axis * half,
            color=GREEN_B,
            stroke_width=3,
            dash_length=0.15,
            stroke_opacity=0.7
        )
        self.inner_axes.add(x_inner)

        x_outer = Arrow(
            start=self.p_center + self.x_axis * half,
            end=self.p_center + self.x_axis * (half + 1.5),
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
            end=self.p_center + self.y_axis * half,
            color=RED_B,
            stroke_width=3,
            dash_length=0.15,
            stroke_opacity=0.7
        )
        self.inner_axes.add(y_inner)

        y_outer = Arrow(
            start=self.p_center + self.y_axis * half,
            end=self.p_center + self.y_axis * (half + 1.5),
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
            end=self.p_center + self.z_axis * (self.height / 2),
            color=BLUE_B,
            stroke_width=3,
            dash_length=0.15,
            stroke_opacity=0.7
        )
        self.inner_axes.add(z_inner)

        z_outer = Arrow(
            start=self.p_center + self.z_axis * (self.height / 2),
            end=self.p_center + self.z_axis * (self.height / 2 + 1.0),
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
            ("A", self.p_bottom_front, DOWN),
            ("B", self.p_bottom_right_back, DOWN + RIGHT),
            ("C", self.p_bottom_left_back, DOWN + LEFT),
        ]

        # 顶点
        labels.append(("S", self.p_apex, UP))

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
            "p_apex": self.p_apex,
            "p_bottom_front": self.p_bottom_front,
            "p_bottom_right_back": self.p_bottom_right_back,
            "p_bottom_left_back": self.p_bottom_left_back,
        }
