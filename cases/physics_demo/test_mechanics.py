"""
斜面滑块受力分析 - 测试演示

这个脚本展示如何使用 InclinedPlaneGroup 组件
包含完整的动画序列和文字说明
"""

from manim import *
import sys
import os
import math
import numpy as np

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from components.physics.mechanics import InclinedPlaneGroup


class TestInclinedPlane(Scene):
    """
    测试场景：斜面滑块受力分析完整演示
    """

    def construct(self):
        # ============================================
        # 第一部分：创建标题
        # ============================================
        title = Text("斜面滑块受力分析", font_size=48).to_edge(UP)
        self.play(Write(title))
        self.wait(1)

        # ============================================
        # 第二部分：创建斜面和滑块（不显示力）
        # ============================================
        # 创建不显示受力的斜面组件
        plane_no_forces = InclinedPlaneGroup(
            angle=30,           # 斜面角度 30 度
            length=5.0,         # 底边长度
            block_width=1.0,    # 滑块宽度
            block_height=0.6,   # 滑块高度
            show_forces=False,  # 暂时不显示力
            show_angle=True     # 显示角度标注
        )

        # 将组件移到屏幕中央
        plane_no_forces.center()

        # 显示斜面和滑块
        self.play(Create(plane_no_forces), run_time=2)
        self.wait(1)

        # ============================================
        # 第三部分：依次显示各个力
        # ============================================
        # 创建带受力的完整组件
        plane_with_forces = InclinedPlaneGroup(
            angle=30,
            length=5.0,
            block_width=1.0,
            block_height=0.6,
            show_forces=True,
            show_angle=True
        )
        plane_with_forces.center()

        # 提取各个力向量（为了单独动画）
        gravity = plane_with_forces.gravity
        normal = plane_with_forces.normal_force
        friction = plane_with_forces.friction

        # 依次显示：重力 -> 支持力 -> 摩擦力
        # ============================================

        # 显示重力 (红色 mg)
        gravity_label = Text("重力 (mg)", font_size=24, color=RED).to_edge(LEFT).shift(UP * 2)
        self.play(
            Create(gravity),
            Write(gravity_label),
            run_time=1.5
        )
        self.wait(0.5)

        # 显示支持力 (蓝色 F_N)
        normal_label = Text("支持力 (F_N)", font_size=24, color=BLUE).to_edge(LEFT).shift(UP)
        self.play(
            Create(normal),
            Write(normal_label),
            run_time=1.5
        )
        self.wait(0.5)

        # 显示摩擦力 (绿色 f)
        friction_label = Text("摩擦力 (f)", font_size=24, color=GREEN).to_edge(LEFT)
        self.play(
            Create(friction),
            Write(friction_label),
            run_time=1.5
        )
        self.wait(1)

        # ============================================
        # 第四部分：添加说明文字
        # ============================================
        explanation = VGroup(
            Text("• 重力：竖直向下", font_size=20, color=RED),
            Text("• 支持力：垂直斜面向上", font_size=20, color=BLUE),
            Text("• 摩擦力：沿斜面向上", font_size=20, color=GREEN),
        ).arrange(DOWN, aligned_edge=LEFT).to_edge(RIGHT).shift(DOWN * 0.5)

        self.play(FadeIn(explanation, shift=LEFT * 0.5))
        self.wait(2)

        # ============================================
        # 第五部分：让滑块沿斜面微微滑动
        # ============================================
        # 计算滑动方向（沿斜面向下）
        angle_rad = 30 * DEGREES
        slide_direction = np.array([math.cos(angle_rad), math.sin(angle_rad), 0])

        # 创建滑动动画（先下滑，再上滑复位）
        block = plane_with_forces.block

        self.play(
            block.animate.shift(slide_direction * 0.5),
            run_time=2,
            rate_func=smooth
        )

        # 同时移动力的箭头（跟随滑块）
        self.play(
            gravity.animate.shift(slide_direction * 0.5),
            normal.animate.shift(slide_direction * 0.5),
            friction.animate.shift(slide_direction * 0.5),
            run_time=1
        )

        self.wait(0.5)

        # 复位
        self.play(
            block.animate.shift(slide_direction * -0.5),
            gravity.animate.shift(slide_direction * -0.5),
            normal.animate.shift(slide_direction * -0.5),
            friction.animate.shift(slide_direction * -0.5),
            run_time=2,
            rate_func=smooth
        )

        self.wait(2)

        # ============================================
        # 第六部分：总结
        # ============================================
        summary = Text(
            "物体在斜面上的受力分析",
            font_size=32,
            color=YELLOW
        ).to_edge(DOWN)

        self.play(Write(summary))
        self.wait(3)

        # ============================================
        # 结束：淡出所有内容
        # ============================================
        self.play(
            FadeOut(VGroup(
                plane_with_forces,
                gravity_label,
                normal_label,
                friction_label,
                explanation,
                summary,
                title
            )),
            run_time=2
        )


class TestDifferentAngles(Scene):
    """
    测试场景：对比不同角度的斜面
    """

    def construct(self):
        title = Text("不同角度对比", font_size=48).to_edge(UP)
        self.play(Write(title))
        self.wait(1)

        # 创建三个不同角度的斜面
        plane_15 = InclinedPlaneGroup(angle=15, length=3, show_forces=True)
        plane_30 = InclinedPlaneGroup(angle=30, length=3, show_forces=True)
        plane_45 = InclinedPlaneGroup(angle=45, length=3, show_forces=True)

        # 排列它们
        plane_15.shift(LEFT * 4)
        plane_30.shift(LEFT * 0.5)
        plane_45.shift(RIGHT * 3.5)

        # 添加角度标签
        label_15 = Text("15°", font_size=24).next_to(plane_15, DOWN)
        label_30 = Text("30°", font_size=24).next_to(plane_30, DOWN)
        label_45 = Text("45°", font_size=24).next_to(plane_45, DOWN)

        # 依次显示
        self.play(Create(plane_15), Write(label_15), run_time=1)
        self.play(Create(plane_30), Write(label_30), run_time=1)
        self.play(Create(plane_45), Write(label_45), run_time=1)

        self.wait(3)


class TestSimple(Scene):
    """
    测试场景：最简单的演示（快速测试用）
    """

    def construct(self):
        # 创建一个简单的斜面组件
        plane = InclinedPlaneGroup(
            angle=30,
            length=5.0,
            show_forces=True
        )

        plane.center()

        # 直接显示
        self.play(Create(plane), run_time=2)
        self.wait(3)

        # 让滑块滑动
        block = plane.block
        angle_rad = 30 * DEGREES
        slide_dir = np.array([math.cos(angle_rad), math.sin(angle_rad), 0])

        self.play(block.animate.shift(slide_dir * 0.8), run_time=2)
        self.wait(2)
