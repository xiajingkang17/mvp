"""
直三棱柱组件 - Triangular Prism Geometry (绝对中心构建法)

实现中国高中教材风格的斜二测直三棱柱可视化。

核心架构（2026-02-19）:
- 采用"绝对中心构建法"（Absolute Center Method）
- 定义绝对的数学中心 p_center，所有组件基于此点生成
- 离散顶点连接法，手动绘制每条边
- 确保 100% 几何精确

作者: Manim 数学组件库
日期: 2026-02-19
"""

from __future__ import annotations

import numpy as np
from manim import *
from typing import List, Tuple, Optional


class TriangularPrismOblique(VGroup):
    """
    斜二测直三棱柱组件（绝对中心构建法）

    核心特性：
    - 定义绝对的数学中心 p_center（定海神针）
    - 所有关键顶点直接基于坐标计算
    - 离散顶点连接法，手动绘制每条边
    - 一个顶点在后（虚线），两个顶点在前（实线）

    参数：
    -------
    side_radius : float
        外接圆半径（默认 2.0，用于定位三角形顶点）
    height : float
        三棱柱高度（默认 3.5）
    skew_factor : float
        压缩比（默认 0.4，用于把底面压扁）
    x_axis_angle : float
        X 轴倾斜角度（默认 -135°，斜二测标准）
    show_axes : bool
        是否显示坐标轴（默认 True）
    show_labels : bool
        是否显示标签（默认 True）
    center : np.ndarray
        底面中心的绝对坐标（默认 ORIGIN）
    **kwargs
        其他 VGroup 参数
    """

    def __init__(
        self,
        side_radius: float = 2.0,
        height: float = 3.5,
        skew_factor: float = 0.4,
        x_axis_angle: float = -135 * DEGREES,
        show_axes: bool = True,
        show_labels: bool = True,
        center: np.ndarray = ORIGIN,
        **kwargs
    ):
        super().__init__(**kwargs)

        # 保存参数
        self.side_radius = side_radius
        self._height = height  # 使用 _height 避免属性冲突
        self.skew_factor = skew_factor
        self.x_axis_angle = x_axis_angle
        self.show_axes = show_axes
        self.show_labels = show_labels

        # ========== 步骤 A: 计算关键顶点（Vertices Calculation）- 定海神针 ==========
        # 不依赖图形，直接算坐标，确保绝对精准

        # A.1 定义三个角度（一个顶点在后，两个顶点在前）
        self.angle_back = 90 * DEGREES    # 后顶点 A（虚线之源）
        self.angle_left = 210 * DEGREES   # 左前顶点 B
        self.angle_right = 330 * DEGREES  # 右前顶点 C

        # A.2 计算底面三个顶点的绝对坐标
        # 公式：x = r * cos(theta), y = r * sin(theta) * skew_factor
        # 别忘了加上 p_center！

        # 底面后顶点 A (90度)
        x_bottom_back = self.side_radius * np.cos(self.angle_back)
        y_bottom_back = self.side_radius * np.sin(self.angle_back) * self.skew_factor
        self.p_center = center  # 🔑 底面中心（定海神针）
        self.p_bottom_back = self.p_center + np.array([x_bottom_back, y_bottom_back, 0])

        # 底面左前顶点 B (210度)
        x_bottom_left = self.side_radius * np.cos(self.angle_left)
        y_bottom_left = self.side_radius * np.sin(self.angle_left) * self.skew_factor
        self.p_bottom_left = self.p_center + np.array([x_bottom_left, y_bottom_left, 0])

        # 底面右前顶点 C (330度)
        x_bottom_right = self.side_radius * np.cos(self.angle_right)
        y_bottom_right = self.side_radius * np.sin(self.angle_right) * self.skew_factor
        self.p_bottom_right = self.p_center + np.array([x_bottom_right, y_bottom_right, 0])

        # A.3 计算顶面三个顶点的绝对坐标（向上平移）
        self.p_top_back = self.p_bottom_back + UP * self._height      # 顶面后顶点 A'
        self.p_top_left = self.p_bottom_left + UP * self._height      # 顶面左前顶点 B'
        self.p_top_right = self.p_bottom_right + UP * self._height    # 顶面右前顶点 C'

        # ========== 步骤 B: 绘制底面（The Base）- 离散顶点连接 ==========
        # 虚线边：连接 p_bottom_back 的两条边是不可见的
        # 实线边：前面的一条边（p_bottom_left -> p_bottom_right）是可见的

        # B.1 后左棱（虚线，不可见）
        self.bottom_back_left = Line(
            start=self.p_bottom_back,
            end=self.p_bottom_left,
            color=GRAY,
            stroke_width=2
        )
        self.bottom_back_left = DashedVMobject(self.bottom_back_left, dashed_ratio=0.5)

        # B.2 后右棱（虚线，不可见）
        self.bottom_back_right = Line(
            start=self.p_bottom_back,
            end=self.p_bottom_right,
            color=GRAY,
            stroke_width=2
        )
        self.bottom_back_right = DashedVMobject(self.bottom_back_right, dashed_ratio=0.5)

        # B.3 前棱（实线，可见）
        self.bottom_front = Line(
            start=self.p_bottom_left,
            end=self.p_bottom_right,
            color=WHITE,
            stroke_width=3
        )

        # ========== 步骤 C: 绘制侧棱（Vertical Edges）==========
        # 后侧棱（虚线，不可见）
        # 前侧棱（实线，可见）

        # C.1 后侧棱（虚线）
        self.edge_back = Line(
            start=self.p_bottom_back,
            end=self.p_top_back,
            color=GRAY,
            stroke_width=2
        )
        self.edge_back = DashedVMobject(self.edge_back, dashed_ratio=0.5)

        # C.2 左前侧棱（实线）
        self.edge_left = Line(
            start=self.p_bottom_left,
            end=self.p_top_left,
            color=WHITE,
            stroke_width=3
        )

        # C.3 右前侧棱（实线）
        self.edge_right = Line(
            start=self.p_bottom_right,
            end=self.p_top_right,
            color=WHITE,
            stroke_width=3
        )

        # ========== 步骤 D: 绘制顶面（The Top）- 完全可见 ==========
        # 顶面完全可见，三条边都是实线

        # D.1 顶面后左棱（实线）
        self.top_back_left = Line(
            start=self.p_top_back,
            end=self.p_top_left,
            color=WHITE,
            stroke_width=3
        )

        # D.2 顶面后右棱（实线）
        self.top_back_right = Line(
            start=self.p_top_back,
            end=self.p_top_right,
            color=WHITE,
            stroke_width=3
        )

        # D.3 顶面前棱（实线）
        self.top_front = Line(
            start=self.p_top_left,
            end=self.p_top_right,
            color=WHITE,
            stroke_width=3
        )

        # ========== 步骤 E: 绘制坐标轴（Axes）- 基于绝对中心 ==========

        if show_axes:
            self._create_axes()

        # ========== 组装组件（层级处理）==========

        # 层级顺序（从下到上）：
        # 1. 底面虚线边
        # 2. 内部坐标轴（虚线）
        # 3. 底面实线边
        # 4. 侧棱（虚线在后，实线在前）
        # 5. 顶面实线边
        # 6. 外部坐标轴
        # 7. 标签

        # 按层级顺序添加
        self.add(self.bottom_back_left)   # 底面后左棱（虚线，最底层）
        self.add(self.bottom_back_right)  # 底面后右棱（虚线）

        if show_axes:
            self.add(self.inner_axes)  # 内部坐标轴

        self.add(self.bottom_front)     # 底面前棱（实线）
        self.add(self.edge_back)        # 后侧棱（虚线）
        self.add(self.edge_left)        # 左前侧棱（实线）
        self.add(self.edge_right)       # 右前侧棱（实线）
        self.add(self.top_back_left)    # 顶面后左棱（实线）
        self.add(self.top_back_right)   # 顶面后右棱（实线）
        self.add(self.top_front)        # 顶面前棱（实线）

        if show_axes:
            self.add(self.outer_axes)  # 外部坐标轴

        if show_labels:
            self._create_labels()
            self.add(self.labels)

    @property
    def height(self) -> float:
        """三棱柱高度（兼容属性）"""
        return self._height

    # ========================================================================
    # 坐标轴系统（基于绝对中心）
    # ========================================================================

    def _create_axes(self):
        """创建坐标轴（基于绝对中心 p_center）"""

        # 分离内部和外部坐标轴
        self.inner_axes = VGroup()
        self.outer_axes = VGroup()

        # ========== Y 轴（水平向右，GREEN）==========
        # 内（虚线）：从 p_center 沿水平向右延伸
        y_inner_length = self.side_radius * 0.8
        y_inner_end = self.p_center + RIGHT * y_inner_length
        y_inner = DashedLine(
            start=self.p_center,          # 🔑 原点 O
            end=y_inner_end,
            color=GREEN_B,
            stroke_width=3,
            dash_length=0.15,
            stroke_opacity=0.7
        )
        self.inner_axes.add(y_inner)

        # 外（实线箭头）：从虚线终点继续延伸
        y_arrow_length = 1.5
        y_outer_end = y_inner_end + RIGHT * y_arrow_length
        y_outer = Arrow(
            start=y_inner_end,
            end=y_outer_end,
            color=GREEN_B,
            stroke_width=4,
            max_tip_length_to_length_ratio=0.15,
            buff=0
        )
        y_label = MathTex("y", font_size=24, color=GREEN_B)
        y_label.move_to(y_outer_end + RIGHT * 0.3)
        self.outer_axes.add(y_outer, y_label)

        # ========== Z 轴（竖直向上，BLUE）==========
        # 内（虚线）：从 p_center 到 p_center + UP * height（中轴线）
        z_inner_end = self.p_center + UP * self._height
        z_inner = DashedLine(
            start=self.p_center,          # 🔑 原点 O
            end=z_inner_end,
            color=BLUE_B,
            stroke_width=3,
            dash_length=0.15,
            stroke_opacity=0.7
        )
        self.inner_axes.add(z_inner)

        # 外（实线箭头）：从虚线终点向上延伸
        z_arrow_length = 1.0
        z_outer_end = z_inner_end + UP * z_arrow_length
        z_outer = Arrow(
            start=z_inner_end,
            end=z_outer_end,
            color=BLUE_B,
            stroke_width=4,
            max_tip_length_to_length_ratio=0.15,
            buff=0
        )
        z_label = MathTex("z", font_size=24, color=BLUE_B)
        z_label.move_to(z_outer_end + UP * 0.3)
        self.outer_axes.add(z_outer, z_label)

        # ========== X 轴（斜向左下，RED）==========
        # 计算方向向量
        x_direction = rotate_vector(RIGHT, self.x_axis_angle)

        # 内（虚线）：从 p_center 沿 X 轴方向延伸
        x_inner_length = self.side_radius * 0.7
        x_inner_end = self.p_center + x_direction * x_inner_length
        x_inner = DashedLine(
            start=self.p_center,          # 🔑 原点 O
            end=x_inner_end,
            color=RED_B,
            stroke_width=3,
            dash_length=0.15,
            stroke_opacity=0.7
        )
        self.inner_axes.add(x_inner)

        # 外（实线箭头）：从虚线终点继续延伸
        x_arrow_length = 1.5
        x_outer_end = x_inner_end + x_direction * x_arrow_length
        x_outer = Arrow(
            start=x_inner_end,
            end=x_outer_end,
            color=RED_B,
            stroke_width=4,
            max_tip_length_to_length_ratio=0.15,
            buff=0
        )
        x_label = MathTex("x", font_size=24, color=RED_B)
        x_label.move_to(x_outer_end + x_direction * 0.5)
        self.outer_axes.add(x_outer, x_label)

    # ========================================================================
    # 标签系统（基于绝对中心）
    # ========================================================================

    def _create_labels(self):
        """创建标签（底面 A,B,C 和顶面 A',B',C'）"""
        self.labels = VGroup()

        # 底面标签（向下偏移）
        label_a = MathTex("A", font_size=24, color=YELLOW)
        label_a.move_to(self.p_bottom_back + DOWN * 0.5)
        self.labels.add(label_a)

        label_b = MathTex("B", font_size=24, color=YELLOW)
        label_b.move_to(self.p_bottom_left + DOWN * 0.5 + LEFT * 0.3)
        self.labels.add(label_b)

        label_c = MathTex("C", font_size=24, color=YELLOW)
        label_c.move_to(self.p_bottom_right + DOWN * 0.5 + RIGHT * 0.3)
        self.labels.add(label_c)

        # 顶面标签（向上偏移）
        label_a_prime = MathTex("A'", font_size=24, color=YELLOW)
        label_a_prime.move_to(self.p_top_back + UP * 0.5)
        self.labels.add(label_a_prime)

        label_b_prime = MathTex("B'", font_size=24, color=YELLOW)
        label_b_prime.move_to(self.p_top_left + UP * 0.5 + LEFT * 0.3)
        self.labels.add(label_b_prime)

        label_c_prime = MathTex("C'", font_size=24, color=YELLOW)
        label_c_prime.move_to(self.p_top_right + UP * 0.5 + RIGHT * 0.3)
        self.labels.add(label_c_prime)

    # ========================================================================
    # 辅助方法（返回绝对坐标）
    # ========================================================================

    def get_center_bottom(self) -> np.ndarray:
        """
        获取底面中心的绝对坐标

        🔑 返回 p_center（定海神针）
        """
        return self.p_center

    def get_center_top(self) -> np.ndarray:
        """
        获取顶面中心的绝对坐标

        🔑 返回 p_center + UP * height
        """
        return self.p_center + UP * self._height

    def get_vertices_bottom(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        获取底面三个顶点（后、左、右）

        🔑 返回计算的绝对坐标：
        - 后顶点：p_bottom_back (90度)
        - 左前顶点：p_bottom_left (210度)
        - 右前顶点：p_bottom_right (330度)
        """
        return self.p_bottom_back, self.p_bottom_left, self.p_bottom_right

    def get_vertices_top(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        获取顶面三个顶点（后、左、右）

        🔑 返回计算的绝对坐标：
        - 后顶点：p_top_back
        - 左前顶点：p_top_left
        - 右前顶点：p_top_right
        """
        return self.p_top_back, self.p_top_left, self.p_top_right

    def get_key_points(self) -> dict:
        """
        获取所有关键点（用于调试和验证）

        Returns:
            dict: 包含所有关键点的字典
        """
        return {
            "p_center": self.p_center,
            "p_bottom_back": self.p_bottom_back,
            "p_bottom_left": self.p_bottom_left,
            "p_bottom_right": self.p_bottom_right,
            "p_top_back": self.p_top_back,
            "p_top_left": self.p_top_left,
            "p_top_right": self.p_top_right,
        }
