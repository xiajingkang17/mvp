"""
球体组件 - Sphere Geometry (绝对中心构建法 + 美术优化版)

实现中国高中教材风格的斜二测球体可视化。

核心架构（2026-02-19 - Enhanced）:
- 采用"绝对中心构建法"（Absolute Center Method）
- 定义绝对的球心 p_center，所有组件基于此点生成
- 解析几何求交点，精确计算坐标轴与球体表面的交点
- 视觉层级优化：外轮廓加粗，内部线条变细
- 新增本初子午线（竖直椭圆），增强立体感
- 新增穿刺点（Dots），明确标出坐标轴穿出位置

作者: Manim 数学组件库
日期: 2026-02-19
版本: Enhanced v2.0
"""

from __future__ import annotations

import numpy as np
from manim import *
from typing import List, Tuple, Optional


class SphereOblique(VGroup):
    """
    斜二测球体组件（绝对中心构建法 + 美术优化版）

    核心特性：
    - 定义绝对的球心 p_center（定海神针）
    - 外轮廓永远是正圆（加粗，stroke_width=4）
    - 赤道是水平椭圆（变细，stroke_width=2，GRAY_B）
    - 本初子午线是竖直椭圆（变细，stroke_width=2，GRAY_B）
    - 穿刺点明确标出坐标轴穿出位置
    - 坐标轴与球体表面的交点通过解析几何精确计算

    参数：
    -------
    radius : float
        球体半径（默认 2.0）
    skew_factor : float
        压缩比（默认 0.3，赤道椭圆扁度，球体的赤道通常画得比圆柱底面更扁）
    x_axis_angle : float
        X 轴倾斜角度（默认 -135°，斜二测标准）
    show_axes : bool
        是否显示坐标轴（默认 True）
    show_labels : bool
        是否显示标签（默认 True）
    show_meridian : bool
        是否显示本初子午线（默认 True，增强立体感）
    show_intersection_dots : bool
        是否显示穿刺点（默认 True，明确标出坐标轴穿出位置）
    center : np.ndarray
        球心的绝对坐标（默认 ORIGIN）
    **kwargs
        其他 VGroup 参数
    """

    def __init__(
        self,
        radius: float = 2.0,
        skew_factor: float = 0.3,
        x_axis_angle: float = -135 * DEGREES,
        show_axes: bool = True,
        show_labels: bool = True,
        show_meridian: bool = True,
        show_intersection_dots: bool = True,
        center: np.ndarray = ORIGIN,
        **kwargs
    ):
        super().__init__(**kwargs)

        # 保存参数
        self.radius = radius
        self.skew_factor = skew_factor
        self.x_axis_angle = x_axis_angle
        self.show_axes = show_axes
        self.show_labels = show_labels
        self.show_meridian = show_meridian
        self.show_intersection_dots = show_intersection_dots

        # ========== 步骤 A: 锁定球心（Sphere Center）- 定海神针 ==========
        self.p_center = center  # 🔑 球心（定海神针）

        # ========== 步骤 B: 绘制外轮廓（The Contour）- 正圆（加粗）==========
        # 视觉层级：外轮廓是最外层的边界，加粗显示
        self.contour = Circle(
            radius=self.radius,
            arc_center=self.p_center,
            stroke_width=4,      # 🔑 加粗（从 3 增加到 4）
            stroke_color=WHITE
        )

        # ========== 步骤 C: 绘制赤道（The Equator）- 水平椭圆（变细）==========
        # 视觉层级：内部结构，变细显示，颜色浅灰
        # 赤道是一个水平放置的椭圆，前后分虚实

        # C.1 前赤道（实线，下半弧：180° -> 360°）
        self.equator_front = Arc(
            radius=self.radius,
            start_angle=PI,                # 180°
            angle=PI,                       # 到 360°
            arc_center=self.p_center,
            stroke_width=2,                # 🔑 变细（内部线条）
            stroke_color=GRAY_B            # 🔑 浅灰色（不抢眼）
        )
        # 压扁成椭圆（关键修复：指定 about_point）
        self.equator_front.stretch(self.skew_factor, dim=1, about_point=self.p_center)

        # C.2 后赤道（虚线，上半弧：0° -> 180°）
        self.equator_back = Arc(
            radius=self.radius,
            start_angle=0,                  # 0°
            angle=PI,                       # 到 180°
            arc_center=self.p_center,
            stroke_width=2,                # 🔑 变细（内部线条）
            stroke_color=GRAY_B            # 🔑 浅灰色（不抢眼）
        )
        # 压扁成椭圆（关键修复：指定 about_point）
        self.equator_back.stretch(self.skew_factor, dim=1, about_point=self.p_center)
        # 转为虚线（dashed_ratio=0.5，让虚线更稀疏）
        self.equator_back = DashedVMobject(self.equator_back, dashed_ratio=0.5)

        # ========== 步骤 D: 绘制本初子午线（The Prime Meridian）- 竖直椭圆 ==========
        # 为了撑起球体的体积感，我们需要一条竖直方向的椭圆

        if show_meridian:
            # D.1 前经线（实线，右半边：-90° -> 90°）
            self.meridian_front = Arc(
                radius=self.radius,
                start_angle=-PI / 2,        # -90°
                angle=PI,                    # 到 90°
                arc_center=self.p_center,
                stroke_width=2,             # 🔑 变细（内部线条）
                stroke_color=GRAY_B         # 🔑 浅灰色（不抢眼）
            )
            # 水平压缩（与赤道扁度一致）
            self.meridian_front.stretch(self.skew_factor, dim=0, about_point=self.p_center)

            # D.2 后经线（虚线，左半边：90° -> 270°）
            self.meridian_back = Arc(
                radius=self.radius,
                start_angle=PI / 2,         # 90°
                angle=PI,                    # 到 270°
                arc_center=self.p_center,
                stroke_width=2,             # 🔑 变细（内部线条）
                stroke_color=GRAY_B         # 🔑 浅灰色（不抢眼）
            )
            # 水平压缩（与赤道扁度一致）
            self.meridian_back.stretch(self.skew_factor, dim=0, about_point=self.p_center)
            # 转为虚线（dashed_ratio=0.5，让虚线更稀疏）
            self.meridian_back = DashedVMobject(self.meridian_back, dashed_ratio=0.5)

        # ========== 步骤 E: 绘制坐标轴（Axes）- 解析几何求交点 ==========

        if show_axes:
            self._create_axes()

        # ========== 步骤 F: 绘制穿刺点（Intersection Dots）==========
        # 明确标出坐标轴穿出球面的位置，消除歧义

        if show_intersection_dots and show_axes:
            self.intersection_dots = VGroup()

            # X 轴穿刺点（红色）
            if hasattr(self, 'p_x_intersect'):
                dot_x = Dot(
                    point=self.p_x_intersect,
                    radius=0.06,            # 🔑 精致的小点
                    color=RED_B,
                    stroke_width=1
                )
                self.intersection_dots.add(dot_x)

            # Y 轴穿刺点（绿色）
            if hasattr(self, 'p_y_intersect'):
                dot_y = Dot(
                    point=self.p_y_intersect,
                    radius=0.06,            # 🔑 精致的小点
                    color=GREEN_B,
                    stroke_width=1
                )
                self.intersection_dots.add(dot_y)

            # Z 轴穿刺点（蓝色）
            if hasattr(self, 'p_z_intersect'):
                dot_z = Dot(
                    point=self.p_z_intersect,
                    radius=0.06,            # 🔑 精致的小点
                    color=BLUE_B,
                    stroke_width=1
                )
                self.intersection_dots.add(dot_z)

        # ========== 组装组件（层级处理 - Z-Index）==========
        # 严格按以下顺序 add()，确保遮挡关系正确：
        # 1. 后赤道（虚）+ 后经线（虚）+ 内坐标轴（虚）  <-- 最底层
        # 2. 外轮廓（圆）
        # 3. 前赤道（实）+ 前经线（实）
        # 4. 穿刺点（Dots）
        # 5. 外坐标轴（实）
        # 6. 标签                                     <-- 最顶层

        # 1. 最底层：后赤道（虚）+ 后经线（虚）
        self.add(self.equator_back)  # 后赤道（虚线，最底层）
        if show_meridian:
            self.add(self.meridian_back)  # 后经线（虚线）

        # 2. 内部坐标轴（虚线）
        if show_axes:
            self.add(self.inner_axes)

        # 3. 外轮廓（正圆）
        self.add(self.contour)

        # 4. 前赤道（实）+ 前经线（实）
        self.add(self.equator_front)  # 前赤道（实线）
        if show_meridian:
            self.add(self.meridian_front)  # 前经线（实线）

        # 5. 穿刺点（Dots）
        if show_intersection_dots and show_axes:
            self.add(self.intersection_dots)

        # 6. 外部坐标轴（实线）
        if show_axes:
            self.add(self.outer_axes)

        # 7. 标签（最顶层）
        if show_labels:
            self._create_labels()
            self.add(self.labels)

    # ========================================================================
    # 坐标轴系统（基于解析几何求交点）
    # ========================================================================

    def _create_axes(self):
        """创建坐标轴（基于解析几何求交点）"""

        # 分离内部和外部坐标轴
        self.inner_axes = VGroup()
        self.outer_axes = VGroup()

        # ========== Y 轴（水平向右，GREEN）==========
        # 交点: p_y_intersect = p_center + RIGHT * radius
        self.p_y_intersect = self.p_center + RIGHT * self.radius

        # 内（虚线）：从 p_center 到 p_y_intersect
        y_inner = DashedLine(
            start=self.p_center,          # 🔑 球心 O
            end=self.p_y_intersect,
            color=GREEN_B,
            stroke_width=3,
            dash_length=0.15,
            stroke_opacity=0.7
        )
        self.inner_axes.add(y_inner)

        # 外（实线箭头）：从 p_y_intersect 向右延伸
        y_arrow_length = 1.5
        y_outer_end = self.p_y_intersect + RIGHT * y_arrow_length
        y_outer = Arrow(
            start=self.p_y_intersect,
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
        # 交点: p_z_intersect = p_center + UP * radius
        self.p_z_intersect = self.p_center + UP * self.radius

        # 内（虚线）：从 p_center 到 p_z_intersect
        z_inner = DashedLine(
            start=self.p_center,          # 🔑 球心 O
            end=self.p_z_intersect,
            color=BLUE_B,
            stroke_width=3,
            dash_length=0.15,
            stroke_opacity=0.7
        )
        self.inner_axes.add(z_inner)

        # 外（实线箭头）：从 p_z_intersect 向上延伸
        z_arrow_length = 1.0
        z_outer_end = self.p_z_intersect + UP * z_arrow_length
        z_outer = Arrow(
            start=self.p_z_intersect,
            end=z_outer_end,
            color=BLUE_B,
            stroke_width=4,
            max_tip_length_to_length_ratio=0.15,
            buff=0
        )
        z_label = MathTex("z", font_size=24, color=BLUE_B)
        z_label.move_to(z_outer_end + UP * 0.3)
        self.outer_axes.add(z_outer, z_label)

        # ========== X 轴（斜向左下，RED）- 关键计算 ==========
        # 数学问题：射线 y = k * x 与椭圆 x²/a² + y²/b² = 1 的交点
        #
        # 已知：
        # - a = radius（椭圆长半轴）
        # - b = radius * skew_factor（椭圆短半轴）
        # - k = tan(x_axis_angle)（射线斜率）
        # - x_axis_angle = -135°（指向左下方）
        #
        # 联立方程：
        #   y = k * x
        #   x²/a² + y²/b² = 1
        #
        # 代入得：x²/a² + (k*x)²/b² = 1
        #        x² * (1/a² + k²/b²) = 1
        #        x² = 1 / (1/a² + k²/b²)
        #        x² = a² * b² / (b² + a² * k²)
        #        x = ± (a * b) / sqrt(b² + a² * k²)
        #
        # 因为 X 轴指向左边（-135°），所以 x 为负值
        # x_intersect = - (a * b) / sqrt(b² + a² * k²)
        # y_intersect = k * x_intersect

        # 计算斜率
        k = np.tan(self.x_axis_angle)

        # 椭圆参数
        a = self.radius
        b = self.radius * self.skew_factor

        # 计算交点（X 轴与赤道椭圆的交点）
        # 注意：X 轴指向左边，所以 x 为负值
        x_intersect = - (a * b) / np.sqrt(b**2 + a**2 * k**2)
        y_intersect = k * x_intersect

        # X 轴交点的绝对坐标
        self.p_x_intersect = self.p_center + np.array([x_intersect, y_intersect, 0])

        # 内（虚线）：从 p_center 到 p_x_intersect
        x_inner = DashedLine(
            start=self.p_center,          # 🔑 球心 O
            end=self.p_x_intersect,
            color=RED_B,
            stroke_width=3,
            dash_length=0.15,
            stroke_opacity=0.7
        )
        self.inner_axes.add(x_inner)

        # 外（实线箭头）：从 p_x_intersect 沿 X 轴方向延伸
        x_arrow_length = 1.5
        x_direction = rotate_vector(RIGHT, self.x_axis_angle)
        x_outer_end = self.p_x_intersect + x_direction * x_arrow_length
        x_outer = Arrow(
            start=self.p_x_intersect,
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
        """创建标签（O 和 N）"""
        self.labels = VGroup()

        # 球心 O（向下偏移，避开坐标轴）
        label_o = MathTex("O", font_size=24, color=YELLOW)
        label_o.move_to(self.p_center + DOWN * 0.5)
        self.labels.add(label_o)

        # 北极点 N（向上偏移）
        if hasattr(self, 'p_z_intersect'):
            label_n = MathTex("N", font_size=24, color=YELLOW)
            label_n.move_to(self.p_z_intersect + UP * 0.3)
            self.labels.add(label_n)

    # ========================================================================
    # 辅助方法（返回绝对坐标）
    # ========================================================================

    def get_center(self) -> np.ndarray:
        """
        获取球心的绝对坐标

        🔑 返回 p_center（定海神针）
        """
        return self.p_center

    def get_north_pole(self) -> np.ndarray:
        """
        获取北极点的绝对坐标

        🔑 返回 p_center + UP * radius
        """
        return self.p_center + UP * self.radius

    def get_equator_front(self) -> Arc:
        """获取前赤道（可见的基准对象）"""
        return self.equator_front

    def get_equator_back(self) -> Arc:
        """获取后赤道（虚线部分）"""
        return self.equator_back

    def get_meridian_front(self) -> Arc:
        """获取前经线（可见的基准对象）"""
        if hasattr(self, 'meridian_front'):
            return self.meridian_front
        return None

    def get_meridian_back(self) -> Arc:
        """获取后经线（虚线部分）"""
        if hasattr(self, 'meridian_back'):
            return self.meridian_back
        return None

    def get_contour(self) -> Circle:
        """获取外轮廓（正圆）"""
        return self.contour

    def get_intersection_dots(self) -> VGroup:
        """获取穿刺点（Dots）"""
        if hasattr(self, 'intersection_dots'):
            return self.intersection_dots
        return None

    def get_key_points(self) -> dict:
        """
        获取所有关键点（用于调试和验证）

        Returns:
            dict: 包含所有关键点的字典
        """
        key_points = {
            "p_center": self.p_center,
        }

        # 如果有坐标轴，添加交点
        if hasattr(self, 'p_x_intersect'):
            key_points["p_x_intersect"] = self.p_x_intersect
        if hasattr(self, 'p_y_intersect'):
            key_points["p_y_intersect"] = self.p_y_intersect
        if hasattr(self, 'p_z_intersect'):
            key_points["p_z_intersect"] = self.p_z_intersect

        return key_points
