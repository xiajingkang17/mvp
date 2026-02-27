"""
圆台组件 - Frustum Geometry (绝对中心构建法)

实现中国高中教材风格的斜二测圆台可视化。

核心架构（2026-02-19）:
- 采用"绝对中心构建法"（Absolute Center Method）
- 定义绝对的数学中心，所有组件基于此点生成
- 包含 about_point 缩放修复
- 混合圆柱与圆锥的逻辑
- 双半径系统（底面半径 R，顶面半径 r）

作者: Manim 数学组件库
日期: 2026-02-19
"""

from __future__ import annotations

import numpy as np
from manim import *
from typing import List, Tuple, Optional


class FrustumOblique(VGroup):
    """
    斜二测圆台组件（绝对中心构建法）

    核心特性：
    - 定义绝对的数学中心，所有组件基于此点生成
    - 双半径系统（底面半径 R，顶面半径 r）
    - 复用圆柱/圆锥的完美逻辑
    - 包含 about_point 缩放修复
    - 确保 100% 几何精确

    参数：
    -------
    bottom_radius : float
        底面半径 R（默认 2.0）
    top_radius : float
        顶面半径 r（默认 1.0，必须小于底面半径）
    height : float
        圆台高度（默认 3.0）
    skew_factor : float
        压缩比（默认 0.4，用于把圆压扁成椭圆）
    x_axis_angle : float
        X 轴倾斜角度（默认 -135°，斜二测标准）
    show_axes : bool
        是否显示坐标轴（默认 True）
    show_labels : bool
        是否显示标签（默认 True）
    center : np.ndarray
        底面圆心的绝对坐标（默认 ORIGIN）
    **kwargs
        其他 VGroup 参数
    """

    def __init__(
        self,
        bottom_radius: float = 2.0,
        top_radius: float = 1.0,
        height: float = 3.0,
        skew_factor: float = 0.4,
        x_axis_angle: float = -135 * DEGREES,
        show_axes: bool = True,
        show_labels: bool = True,
        center: np.ndarray = ORIGIN,
        **kwargs
    ):
        super().__init__(**kwargs)

        # 保存参数
        self.bottom_radius = bottom_radius
        self.top_radius = top_radius
        self._height = height  # 使用 _height 避免属性冲突
        self.skew_factor = skew_factor
        self.x_axis_angle = x_axis_angle
        self.show_axes = show_axes
        self.show_labels = show_labels

        # ========== 步骤 A: 锁定关键点（Key Points）- 定海神针 ==========
        # 不依赖图形，直接算坐标，确保绝对精准

        # A.1 底面中心（基于绝对中心）
        self.p_center_bottom = center                     # 🔑 底面圆心 O
        self.p_center_top = self.p_center_bottom + UP * self._height  # 🔑 顶面圆心 O'

        # A.2 下底面关键点（使用 bottom_radius）
        self.p_bottom_left = self.p_center_bottom + LEFT * self.bottom_radius    # 🔑 底面左端点
        self.p_bottom_right = self.p_center_bottom + RIGHT * self.bottom_radius   # 🔑 底面右端点

        # A.3 上底面关键点（使用 top_radius）
        self.p_top_left = self.p_center_top + LEFT * self.top_radius          # 🔑 顶面左端点
        self.p_top_right = self.p_center_top + RIGHT * self.top_radius         # 🔑 顶面右端点

        # ========== 步骤 B: 绘制底面（The Bottom Base）- 复用圆柱逻辑 ==========
        # 显式指定 arc_center=p_center_bottom，确保中心绝对精确

        # B.1 前半段（实线，180° -> 360°）
        self.bottom_front_arc = Arc(
            radius=self.bottom_radius,
            start_angle=PI,                # 180°
            angle=PI,                       # 到 360°
            arc_center=self.p_center_bottom, # 🔑 强制指定圆心位置
            stroke_width=3,
            stroke_color=WHITE
        )
        # 压扁成椭圆（关键修复：指定 about_point）
        self.bottom_front_arc.stretch(self.skew_factor, dim=1, about_point=self.p_center_bottom)

        # B.2 后半段（虚线，0° -> 180°）
        self.bottom_back_arc = Arc(
            radius=self.bottom_radius,
            start_angle=0,                  # 0°
            angle=PI,                       # 到 180°
            arc_center=self.p_center_bottom, # 🔑 强制指定圆心位置
            stroke_width=3,
            stroke_color=GRAY
        )
        # 压扁成椭圆（关键修复：指定 about_point）
        self.bottom_back_arc.stretch(self.skew_factor, dim=1, about_point=self.p_center_bottom)
        # 转为虚线
        self.bottom_back_arc = DashedVMobject(self.bottom_back_arc, dashed_ratio=0.5)

        # ========== 步骤 C: 绘制顶面（The Top Base）- 使用 top_radius ==========
        # 直接使用完整椭圆，arc_center=p_center_top

        self.top_ellipse = Ellipse(
            width=2 * self.top_radius,
            height=2 * self.top_radius * self.skew_factor,
            arc_center=self.p_center_top,    # 🔑 强制指定圆心位置
            stroke_width=3,
            stroke_color=WHITE
        )

        # ========== 步骤 D: 绘制侧棱（Side Lines）- 连接上下对应端点 ==========
        # 因为上下椭圆扁率一致，直接连接端点即为视觉切线

        # D.1 左侧棱：连接底面左端点与顶面左端点
        self.left_edge = Line(
            start=self.p_bottom_left,       # 🔑 基于计算的坐标
            end=self.p_top_left,             # 🔑 基于计算的坐标
            color=WHITE,
            stroke_width=3
        )

        # D.2 右侧棱：连接底面右端点与顶面右端点
        self.right_edge = Line(
            start=self.p_bottom_right,      # 🔑 基于计算的坐标
            end=self.p_top_right,            # 🔑 基于计算的坐标
            color=WHITE,
            stroke_width=3
        )

        # ========== 步骤 E: 绘制坐标轴（Axes）- 基于绝对中心 ==========

        if show_axes:
            self._create_axes()

        # ========== 组装组件（层级处理）==========

        # 层级顺序（从下到上）：
        # 1. 底面后弧（虚线）
        # 2. 内部坐标轴（虚线）
        # 3. 底面前弧（实线）
        # 4. 侧棱
        # 5. 顶面椭圆
        # 6. 外部坐标轴
        # 7. 标签

        # 按层级顺序添加
        self.add(self.bottom_back_arc)  # 底面后弧（虚线，最底层）

        if show_axes:
            self.add(self.inner_axes)  # 内部坐标轴

        self.add(self.bottom_front_arc)  # 底面前弧（实线）
        self.add(self.left_edge)       # 左侧棱
        self.add(self.right_edge)      # 右侧棱
        self.add(self.top_ellipse)     # 顶面椭圆

        if show_axes:
            self.add(self.outer_axes)  # 外部坐标轴

        if show_labels:
            self._create_labels()
            self.add(self.labels)

    @property
    def height(self) -> float:
        """圆台高度（兼容属性）"""
        return self._height

    # ========================================================================
    # 坐标轴系统（基于绝对中心）
    # ========================================================================

    def _create_axes(self):
        """创建坐标轴（基于绝对中心）"""

        # 分离内部和外部坐标轴
        self.inner_axes = VGroup()
        self.outer_axes = VGroup()

        # ========== Y 轴（水平向右，GREEN）==========
        # 内（虚线）：从 p_center_bottom 到 p_bottom_right（贴合底面半径）
        y_inner = DashedLine(
            start=self.p_center_bottom,     # 🔑 原点 O
            end=self.p_bottom_right,        # 🔑 底面右端点
            color=GREEN_B,
            stroke_width=3,
            dash_length=0.15,
            stroke_opacity=0.7
        )
        self.inner_axes.add(y_inner)

        # 外（实线箭头）：从 p_bottom_right 向右延伸
        y_arrow_length = 1.5
        y_outer = Arrow(
            start=self.p_bottom_right,      # 🔑 从底面右端点开始
            end=self.p_bottom_right + RIGHT * y_arrow_length,
            color=GREEN_B,
            stroke_width=4,
            max_tip_length_to_length_ratio=0.15,
            buff=0
        )
        y_label = MathTex("y", font_size=24, color=GREEN_B)
        y_label.move_to(y_outer.get_end() + RIGHT * 0.3)
        self.outer_axes.add(y_outer, y_label)

        # ========== Z 轴（竖直向上，BLUE）==========
        # 内（虚线）：从 p_center_bottom 到 p_center_top（圆台的高）
        z_inner = DashedLine(
            start=self.p_center_bottom,     # 🔑 原点 O
            end=self.p_center_top,           # 🔑 顶面圆心 O'
            color=BLUE_B,
            stroke_width=3,
            dash_length=0.15,
            stroke_opacity=0.7
        )
        self.inner_axes.add(z_inner)

        # 外（实线箭头）：从 p_center_top 向上延伸
        z_arrow_length = 1.0
        z_outer = Arrow(
            start=self.p_center_top,        # 🔑 从顶面圆心开始
            end=self.p_center_top + UP * z_arrow_length,
            color=BLUE_B,
            stroke_width=4,
            max_tip_length_to_length_ratio=0.15,
            buff=0
        )
        z_label = MathTex("z", font_size=24, color=BLUE_B)
        z_label.move_to(z_outer.get_end() + UP * 0.3)
        self.outer_axes.add(z_outer, z_label)

        # ========== X 轴（斜向左下，RED）==========
        # 计算方向向量
        x_direction = rotate_vector(RIGHT, self.x_axis_angle)

        # 内（虚线）：从 p_center_bottom 沿 X 轴方向延伸
        x_inner_length = self.bottom_radius * 0.7
        x_inner_end = self.p_center_bottom + x_direction * x_inner_length
        x_inner = DashedLine(
            start=self.p_center_bottom,     # 🔑 原点 O
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
        """创建标签（O 和 O'）"""
        self.labels = VGroup()

        # 底面圆心 O（向下偏移，避开坐标轴）
        label_o = MathTex("O", font_size=24, color=YELLOW)
        label_o.move_to(self.p_center_bottom + DOWN * 0.5)
        self.labels.add(label_o)

        # 顶面圆心 O'（向上偏移）
        label_o_prime = MathTex("O'", font_size=24, color=YELLOW)
        label_o_prime.move_to(self.p_center_top + UP * 0.5)
        self.labels.add(label_o_prime)

    # ========================================================================
    # 辅助方法（返回绝对坐标）
    # ========================================================================

    def get_center_bottom(self) -> np.ndarray:
        """
        获取底面圆心的绝对坐标

        🔑 返回 p_center_bottom（定海神针）
        """
        return self.p_center_bottom

    def get_center_top(self) -> np.ndarray:
        """
        获取顶面圆心的绝对坐标

        🔑 返回 p_center_top
        """
        return self.p_center_top

    def get_side_edge_points_bottom(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        获取底面侧棱端点（左、右）

        🔑 返回计算的绝对坐标：
        - 左端点：p_bottom_left = p_center_bottom + LEFT * bottom_radius
        - 右端点：p_bottom_right = p_center_bottom + RIGHT * bottom_radius
        """
        return self.p_bottom_left, self.p_bottom_right

    def get_side_edge_points_top(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        获取顶面侧棱端点（左、右）

        🔑 返回计算的绝对坐标：
        - 左端点：p_top_left = p_center_top + LEFT * top_radius
        - 右端点：p_top_right = p_center_top + RIGHT * top_radius
        """
        return self.p_top_left, self.p_top_right

    def get_bottom_front_arc(self) -> Arc:
        """获取底面前弧（可见的基准对象）"""
        return self.bottom_front_arc

    def get_bottom_back_arc(self) -> Arc:
        """获取底面后弧（虚线部分）"""
        return self.bottom_back_arc

    def get_top_ellipse(self) -> Ellipse:
        """获取顶面椭圆"""
        return self.top_ellipse

    def get_key_points(self) -> dict:
        """
        获取所有关键点（用于调试和验证）

        Returns:
            dict: 包含所有关键点的字典
        """
        return {
            "p_center_bottom": self.p_center_bottom,
            "p_center_top": self.p_center_top,
            "p_bottom_left": self.p_bottom_left,
            "p_bottom_right": self.p_bottom_right,
            "p_top_left": self.p_top_left,
            "p_top_right": self.p_top_right,
        }
