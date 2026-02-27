"""
解析几何组件测试 - Analytic Geometry Tests

测试标准椭圆、双曲线、抛物线、圆等组件的渲染效果
"""

from manim import *
import sys
import os

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from components.math.analytic_geometry import (
    StandardEllipse,
    StandardHyperbola,
    StandardParabola
)
from components.math.simple_circle import StandardCircle


class TestStandardCircle(Scene):
    """
    测试标准圆组件 - 教科书级坐标系演示

    展示：
    - 使用教科书级坐标轴（带 x, y, O 标签）
    - 两个不同圆对比：一个在原点，一个在 (3, 2)
    """

    def construct(self):
        # ============================
        # 1. 构建教科书级坐标轴
        # ============================
        axes = Axes(
            x_range=[-2, 7, 1],
            y_range=[-2, 5, 1],
            x_length=10,
            y_length=8,
            color=WHITE,
            axis_config={
                "include_ticks": True,
                "include_numbers": False,
                "stroke_width": 2,
            }
        )

        # 添加坐标轴标签：x, y, O
        x_label = MathTex(r"x", font_size=32, color=WHITE)
        x_label.next_to(axes.x_axis, RIGHT, buff=0.2)

        y_label = MathTex(r"y", font_size=32, color=WHITE)
        y_label.next_to(axes.y_axis, UP, buff=0.2)

        o_label = MathTex(r"O", font_size=28, color=WHITE)
        o_label.next_to(axes.c2p(0, 0), DOWN + LEFT, buff=0.15)

        axes_labels = VGroup(x_label, y_label, o_label)

        # 标题
        title = Text("标准圆 (Standard Circle)", font_size=36).to_edge(UP)

        # ============================
        # 2. 创建两个圆进行对比
        # ============================

        # 圆 A：标准圆（半径 2，圆心在原点）
        circle_a = StandardCircle(
            radius=2.0,
            center_point=[0, 0, 0],
            show_center_dot=True,
            show_center_coords=True,
            show_radius_line=True,
            show_radius_value=True,
            color=WHITE
        )

        # 圆 B：自定义圆（半径 1.5，圆心在 (3, 2)，红色）
        circle_b = StandardCircle(
            radius=1.5,
            center_point=[3, 2, 0],
            show_center_dot=True,
            show_center_coords=True,
            show_radius_line=True,
            show_radius_value=True,
            color=RED
        )

        # 添加说明标签
        label_a = Text(r"圆 A（标准）", font_size=18, color=WHITE)
        label_a.next_to(circle_a, DOWN, buff=0.5)

        label_b = Text(r"圆 B（自定义）", font_size=18, color=RED)
        label_b.next_to(circle_b, DOWN, buff=0.5)

        # 方程标签
        eq_a = MathTex(r"x^2+y^2=4", font_size=18, color=WHITE)
        eq_a.next_to(label_a, DOWN, buff=0.3)

        eq_b = MathTex(r"(x-3)^2+(y-2)^2=2.25", font_size=18, color=RED)
        eq_b.next_to(label_b, DOWN, buff=0.3)

        # ============================
        # 3. 动画演示
        # ============================

        # Step 1: 画出标题
        self.play(Write(title), run_time=0.6)
        self.wait(0.3)

        # Step 2: 写出坐标轴和标签
        self.play(
            Write(axes),
            Write(axes_labels),
            run_time=1.5
        )
        self.wait(0.5)

        # Step 3: 同时创建两个圆
        self.play(
            Create(circle_a),
            Create(circle_b),
            run_time=2.0
        )

        # Step 4: 显示标签和方程
        self.play(
            FadeIn(VGroup(label_a, label_b, eq_a, eq_b)),
            run_time=0.8
        )

        self.wait(3.0)
