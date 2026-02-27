"""
标准直线组件测试 - Standard Line Test

演示直线的五种方程形式
"""

from manim import *
import sys
import os

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from components.math.analytic_line import StandardLine


class TestStandardLine(Scene):
    """
    测试标准直线组件

    展示一条斜线，包含：
    - 直线本身
    - 两个端点
    - 截距标记
    - 五种方程形式
    """

    def construct(self):
        # 创建教科书级坐标轴
        axes = Axes(
            x_range=[-6, 6, 1],
            y_range=[-4, 4, 1],
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
        title = Text("标准直线 (Standard Line)", font_size=36).to_edge(UP)

        # 创建一条斜线：从 (-3, -2) 到 (3, 4)
        # 这条线应该有明显的斜率和截距
        line = StandardLine(
            point1=[-3, -2],
            point2=[3, 4],
            length=8.0,
            show_equations=True,
            show_intercepts=True,
            color=WHITE
        )

        # 动画演示
        self.play(Write(title), run_time=0.6)
        self.wait(0.3)

        self.play(
            Write(axes),
            Write(axes_labels),
            run_time=1.5
        )
        self.wait(0.5)

        self.play(Create(line), run_time=2.0)

        self.wait(3.0)
