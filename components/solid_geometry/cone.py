"""
圆锥组件 - Cone Geometry (绝对中心构建法)

实现中国高中教材风格的斜二测圆锥可视化。

核心架构（2026-02-19）:
- 采用"绝对中心构建法"（Absolute Center Method）
- 定义绝对的数学中心 p_center，所有组件基于此点生成
- 复用圆柱的完美逻辑，包含 about_point 缩放修复
- 确保 100% 几何精确

作者: Manim 数学组件库
日期: 2026-02-19
"""

from __future__ import annotations

import numpy as np
from manim import *
from typing import List, Tuple, Optional


class ConeOblique(VGroup):
    """
    斜二测圆锥组件（绝对中心构建法）

    核心特性：
    - 定义绝对的数学中心 p_center（定海神针）
    - 所有关键点直接基于坐标计算
    - 不依赖 Mobject 的边界框，避免原点偏移
    - 复用圆柱的完美逻辑，确保几何精确

    参数：
    -------
    radius : float
        底面半径（默认 2.0）
    height : float
        圆锥高度（默认 3.5）
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
        radius: float = 2.0,
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
        self.radius = radius
        self._height = height  # 使用 _height 避免与 Manim 属性冲突
        self.skew_factor = skew_factor
        self.x_axis_angle = x_axis_angle
        self.show_axes = show_axes
        self.show_labels = show_labels

        # ========== 步骤 A: 锁定关键点（Key Points）- 定海神针 ==========
        # 不依赖图形，直接算坐标，确保绝对精准

        # A.1 底面关键点（基于绝对中心 center）
        self.p_center = center                  # 🔑 底面圆心（定海神针）
        self.p_left = self.p_center + LEFT * self.radius    # 🔑 底面左端点
        self.p_right = self.p_center + RIGHT * self.radius   # 🔑 底面右端点

        # A.2 顶点（基于底面中心 + 向上平移）
        self.p_apex = self.p_center + UP * self._height  # 🔑 顶点 S

        # ========== 步骤 B: 计算精确切点（Tangent Points）- 关键优化！ ==========
        # 数学原理：从顶点向底面椭圆引切线，计算切点坐标
        # 设椭圆长半轴 a = radius, 短半轴 b = radius * skew_factor
        # 顶点高度 h = _height
        # 切点的 y 坐标相对于底面中心的偏移量为：y_offset = b^2 / h
        # 切点的 x 坐标相对于底面中心的偏移量为：x_offset = a * sqrt(1 - b^2/h^2)

        a = self.radius
        b = self.radius * self.skew_factor
        h = self._height

        # 计算偏移量
        # 注意：防止 h 太小导致根号下为负数（虽然在圆锥里 h 肯定大于 b）
        if h <= b + 0.001:
            # 如果高度极低，退化为连接端点（保护措施）
            tangent_x_offset = a
            tangent_y_offset = 0
        else:
            tangent_y_offset = (b**2) / h
            tangent_x_offset = a * np.sqrt(1 - (b**2 / h**2))

        # 计算绝对切点坐标（基于底面中心 p_center）
        self.p_tangent_left = self.p_center + LEFT * tangent_x_offset + UP * tangent_y_offset
        self.p_tangent_right = self.p_center + RIGHT * tangent_x_offset + UP * tangent_y_offset

        # ========== 步骤 C: 绘制底面（The Base）- 完全复用圆柱逻辑 ==========
        # 显式指定 arc_center=p_center，确保中心绝对精确
        # 务必包含 about_point 参数，避免裂缝

        # B.1 前半段（实线，180° -> 360°）
        self.base_front_arc = Arc(
            radius=self.radius,
            start_angle=PI,                # 180°
            angle=PI,                       # 到 360°
            arc_center=self.p_center,       # 🔑 强制指定圆心位置
            stroke_width=3,
            stroke_color=WHITE
        )
        # 压扁成椭圆（关键修复：指定 about_point=self.p_center，避免裂缝）
        self.base_front_arc.stretch(self.skew_factor, dim=1, about_point=self.p_center)

        # B.2 后半段（虚线，0° -> 180°）
        self.base_back_arc = Arc(
            radius=self.radius,
            start_angle=0,                  # 0°
            angle=PI,                       # 到 180°
            arc_center=self.p_center,       # 🔑 强制指定圆心位置
            stroke_width=3,
            stroke_color=GRAY
        )
        # 压扁成椭圆（关键修复：指定 about_point=self.p_center，避免裂缝）
        self.base_back_arc.stretch(self.skew_factor, dim=1, about_point=self.p_center)
        # 转为虚线
        self.base_back_arc = DashedVMobject(self.base_back_arc, dashed_ratio=0.5)

        # ========== 步骤 D: 绘制侧棱（Side Lines）- 连接精确切点与顶点 ==========
        # 使用精确切点，获得完美的视觉相切效果

        # D.1 左母线：连接左切点与顶点
        self.left_edge = Line(
            start=self.p_tangent_left,    # 🔑 使用精确切点
            end=self.p_apex,                 # 🔑 顶点 S
            color=WHITE,
            stroke_width=3
        )

        # D.2 右母线：连接右切点与顶点
        self.right_edge = Line(
            start=self.p_tangent_right,  # 🔑 使用精确切点
            end=self.p_apex,                 # 🔑 顶点 S
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
        # 4. 侧棱（母线）
        # 5. 外部坐标轴
        # 6. 标签

        # 按层级顺序添加
        self.add(self.base_back_arc)  # 底面后弧（虚线，最底层）

        if show_axes:
            self.add(self.inner_axes)  # 内部坐标轴

        self.add(self.base_front_arc)  # 底面前弧（实线）
        self.add(self.left_edge)       # 左母线
        self.add(self.right_edge)      # 右母线

        if show_axes:
            self.add(self.outer_axes)  # 外部坐标轴

        if show_labels:
            self._create_labels()
            self.add(self.labels)

    def get_cone_height(self) -> float:
        """圆锥高度"""
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
        # 内（虚线）：从 p_center 到 p_right（完美贴合底面半径）
        y_inner = DashedLine(
            start=self.p_center,          # 🔑 原点 O
            end=self.p_right,             # 🔑 底面右端点
            color=GREEN_B,
            stroke_width=3,
            dash_length=0.15,
            stroke_opacity=0.7
        )
        self.inner_axes.add(y_inner)

        # 外（实线箭头）：从 p_right 向右延伸
        y_arrow_length = 1.5
        y_outer = Arrow(
            start=self.p_right,             # 🔑 从底面右端点开始
            end=self.p_right + RIGHT * y_arrow_length,
            color=GREEN_B,
            stroke_width=4,
            max_tip_length_to_length_ratio=0.15,
            buff=0
        )
        y_label = MathTex("y", font_size=24, color=GREEN_B)
        y_label.move_to(y_outer.get_end() + RIGHT * 0.3)
        self.outer_axes.add(y_outer, y_label)

        # ========== Z 轴（竖直向上，BLUE）==========
        # 内（虚线）：从 p_center 到 p_apex（圆锥的高）
        z_inner = DashedLine(
            start=self.p_center,          # 🔑 原点 O
            end=self.p_apex,                 # 🔑 顶点 S
            color=BLUE_B,
            stroke_width=3,
            dash_length=0.15,
            stroke_opacity=0.7
        )
        self.inner_axes.add(z_inner)

        # 外（实线箭头）：从 p_apex 向上延伸
        z_arrow_length = 1.0
        z_outer = Arrow(
            start=self.p_apex,                # 🔑 从顶点 S 开始
            end=self.p_apex + UP * z_arrow_length,
            color=BLUE_B,
            stroke_width=4,
            max_tip_length_to_length_ratio=0.15,
            buff=0
        )
        z_label = MathTex("z", font_size=24, color=BLUE_B)
        z_label.move_to(z_outer.get_end() + UP * 0.3)
        self.outer_axes.add(z_outer, z_label)

        # ========== 高度标注线（可选，从底面中心到顶点）==========
        self.height_line_inner = DashedLine(
            start=self.p_center,
            end=self.p_apex,
            color=GRAY,
            stroke_width=2,
            stroke_opacity=0.5,
            dash_length=0.1
        )
        self.add(self.height_line_inner)

        # ========== X 轴（斜向左下，RED）==========
        # 计算方向向量
        x_direction = rotate_vector(RIGHT, self.x_axis_angle)

        # 内（虚线）：从 p_center 沿 X 轴方向延伸
        x_inner_length = self.radius * 0.7
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
        """创建标签（O 和 S）"""
        self.labels = VGroup()

        # 底面圆心 O（向下偏移，避开坐标轴）
        label_o = MathTex("O", font_size=24, color=YELLOW)
        label_o.move_to(self.p_center + DOWN * 0.5)
        self.labels.add(label_o)

        # 顶点 S（向上偏移）
        label_s = MathTex("S", font_size=24, color=YELLOW)
        label_s.move_to(self.p_apex + UP * 0.3)
        self.labels.add(label_s)

    # ========================================================================
    # 辅助方法（返回绝对坐标）
    # ========================================================================

    def get_center_bottom(self) -> np.ndarray:
        """
        获取底面圆心的绝对坐标

        🔑 返回 p_center（定海神针）
        """
        return self.p_center

    def get_apex(self) -> np.ndarray:
        """
        获取顶点的绝对坐标

        🔑 返回 p_apex（顶点 S）
        """
        return self.p_apex

    def get_side_edge_points_bottom(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        获取底面侧棱端点（左、右）

        🔑 返回计算的绝对坐标：
        - 左端点：p_left = p_center + LEFT * radius
        - 右端点：p_right = p_center + RIGHT * radius
        """
        return self.p_left, self.p_right

    def get_base_front_arc(self) -> Arc:
        """
        获取底面前弧（可见的基准对象）

        注意：此对象的 get_center() 可能不准确
        应该使用 get_center_bottom() 获取真正的圆心
        """
        return self.base_front_arc

    def get_base_back_arc(self) -> Arc:
        """获取底面后弧（虚线部分）"""
        return self.base_back_arc

    def get_key_points(self) -> dict:
        """
        获取所有关键点（用于调试和验证）

        Returns:
            dict: 包含所有关键点的字典
        """
        return {
            "p_center": self.p_center,
            "p_left": self.p_left,
            "p_right": self.p_right,
            "p_apex": self.p_apex,
        }
