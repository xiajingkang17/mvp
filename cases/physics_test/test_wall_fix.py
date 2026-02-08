"""
Wall 组件修复验证

单独展示 Wall 组件，查看阴影线效果
"""

from manim import *
import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from components.physics.mechanics_full import Wall


class TestWallFixed(Scene):
    """
    单独展示修复后的 Wall 组件
    """

    def construct(self):
        # 标题
        title = Text("Wall (墙面/地面) 组件修复效果", font_size=42).to_edge(UP)
        self.add(title)

        # 创建 Wall 组件（标准尺寸）
        wall = Wall(
            length=8.0,
            hatch_spacing=0.4,
            hatch_length=0.25,
            color=WHITE,
            stroke_width=4.0
        )

        # 居中显示
        wall.center()

        # 添加标签
        label1 = Text("主表面（白色直线）", font_size=24, color=WHITE)
        label1.next_to(wall, UP, buff=1.0)

        label2 = Text("阴影线（向右下方倾斜 -45°）", font_size=24, color=YELLOW)
        label2.next_to(wall, DOWN, buff=1.0)

        # 标注说明
        explanation = VGroup(
            Text("✓ 短斜线（非垂直线）", font_size=20, color=GREEN),
            Text("✓ -45度倾斜方向", font_size=20, color=GREEN),
            Text("✓ 位于主直线下方", font_size=20, color=GREEN),
            Text("✓ 紧密整齐排列", font_size=20, color=GREEN),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        explanation.to_edge(RIGHT).shift(LEFT * 1.0)

        # 显示所有内容
        self.play(Create(wall), run_time=1)
        self.play(Write(label1), Write(label2))
        self.play(FadeIn(explanation, shift=RIGHT * 0.5))

        self.wait(2)

        # 放大查看细节
        self.play(
            wall.animate.scale(1.5),
            label1.animate.shift(UP * 0.5),
            label2.animate.shift(DOWN * 0.5),
            run_time=1
        )

        self.wait(2)


class TestWallComparison(Scene):
    """
    对比展示：不同尺寸的 Wall
    """

    def construct(self):
        title = Text("Wall 组件 - 不同尺寸对比", font_size=36).to_edge(UP)
        self.add(title)

        # 创建3个不同尺寸的 Wall
        wall1 = Wall(length=4.0, hatch_spacing=0.3)
        wall2 = Wall(length=6.0, hatch_spacing=0.4)
        wall3 = Wall(length=8.0, hatch_spacing=0.5)

        # 添加标签
        label1 = Text("length=4.0\nspacing=0.3", font_size=16)
        label2 = Text("length=6.0\nspacing=0.4", font_size=16)
        label3 = Text("length=8.0\nspacing=0.5", font_size=16)

        group1 = VGroup(wall1, label1).arrange(DOWN, buff=0.3)
        group2 = VGroup(wall2, label2).arrange(DOWN, buff=0.3)
        group3 = VGroup(wall3, label3).arrange(DOWN, buff=0.3)

        # 排列
        row = VGroup(group1, group2, group3)
        row.arrange(DOWN, buff=1.5)
        row.center()

        # 依次显示
        for group in [group1, group2, group3]:
            self.play(Create(group), run_time=0.8)
            self.wait(0.5)

        self.wait(2)


class TestWallDetail(Scene):
    """
    细节展示：放大查看阴影线
    """

    def construct(self):
        # 创建一个较短的 Wall，方便放大查看
        wall = Wall(
            length=6.0,
            hatch_spacing=0.5,
            hatch_length=0.3,
            stroke_width=6.0  # 更粗的线条
        )

        wall.center()

        # 放大2倍
        wall.scale(2.0)

        # 添加标注箭头
        arrow1 = Arrow(
            start=[-2, 0.5, 0],
            end=[-2, -0.5, 0],
            color=YELLOW,
            stroke_width=4
        )

        arrow2 = Arrow(
            start=[0, 0.5, 0],
            end=[0, -0.5, 0],
            color=YELLOW,
            stroke_width=4
        )

        # 标注文字
        note1 = Text("阴影线", font_size=24, color=YELLOW).next_to(arrow1, LEFT)
        note2 = Text("-45°", font_size=24, color=YELLOW).next_to(arrow2, RIGHT)

        # 标题
        title = Text("Wall 组件细节（放大2倍）", font_size=32).to_edge(UP)

        self.add(title)
        self.play(Create(wall), run_time=1)
        self.play(Create(arrow1), Create(arrow2), Write(note1), Write(note2))
        self.wait(3)
