"""
InclinedPlane 组件修复验证

单独展示斜面组件，验证几何逻辑和角度标注
"""

from manim import *
import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from components.physics.mechanics_full import InclinedPlane


class TestInclinedPlaneFixed(Scene):
    """
    展示修复后的 InclinedPlane 组件
    """

    def construct(self):
        # 标题
        title = Text("InclinedPlane (斜面) 组件修复效果", font_size=42).to_edge(UP)
        self.add(title)

        # 创建斜面（30度）
        plane = InclinedPlane(
            angle=30,
            length=5.0,
            show_angle=True
        )

        plane.center()

        # 添加标注说明
        # 左下角标注
        label_left = Text("左下角：直角 (90°)", font_size=20, color=GREEN)
        label_left.next_to(plane, LEFT).shift(UP * 0.5)

        # 右下角标注
        label_right = Text("右下角：斜面底角 θ", font_size=20, color=YELLOW)
        label_right.next_to(plane, RIGHT).shift(DOWN * 0.5)

        # 顶点标注
        label_top = Text("左上角：顶点", font_size=20, color=BLUE)
        label_top.next_to(plane, UP).shift(LEFT * 0.5)

        # 显示所有内容
        self.play(Create(plane), run_time=1)
        self.play(
            FadeIn(label_left),
            FadeIn(label_right),
            FadeIn(label_top),
            run_time=0.5
        )

        self.wait(2)

        # 放大查看角度标注
        self.play(plane.animate.scale(1.5), run_time=1)
        self.wait(2)


class TestInclinedPlaneComparison(Scene):
    """
    对比展示：不同角度的斜面
    """

    def construct(self):
        title = Text("不同角度的斜面对比", font_size=36).to_edge(UP)
        self.add(title)

        # 创建3个不同角度的斜面
        plane1 = InclinedPlane(angle=15, length=4.0)
        plane2 = InclinedPlane(angle=30, length=4.0)
        plane3 = InclinedPlane(angle=45, length=4.0)

        # 添加标签
        label1 = Text("θ = 15°", font_size=18)
        label2 = Text("θ = 30°", font_size=18)
        label3 = Text("θ = 45°", font_size=18)

        group1 = VGroup(plane1, label1).arrange(DOWN, buff=0.3)
        group2 = VGroup(plane2, label2).arrange(DOWN, buff=0.3)
        group3 = VGroup(plane3, label3).arrange(DOWN, buff=0.3)

        # 排列
        row = VGroup(group1, group2, group3)
        row.arrange(RIGHT, buff=1.5)
        row.center()

        # 依次显示
        for group in [group1, group2, group3]:
            self.play(Create(group), run_time=0.8)
            self.wait(0.5)

        self.wait(2)


class TestInclinedPlaneDetail(Scene):
    """
    细节展示：放大查看角度标注
    """

    def construct(self):
        # 创建一个45度的斜面（角度更大，更容易看清）
        plane = InclinedPlane(
            angle=45,
            length=6.0,
            stroke_width=6.0
        )

        plane.center()

        # 放大2倍
        plane.scale(2.0)

        # 添加箭头标注顶点
        vertices = plane[0].get_vertices()

        # 左下角（直角）
        dot_left = Dot(point=ORIGIN, color=GREEN, radius=0.08)
        arrow_left = Arrow(
            start=LEFT * 2 + UP * 0.5,
            end=LEFT * 0.5,
            color=GREEN
        )
        label_left = Text("直角 (90°)", font_size=20, color=GREEN).next_to(arrow_left, LEFT)

        # 右下角（斜面底角 θ）
        dot_right = Dot(point=RIGHT * 6, color=YELLOW, radius=0.08)
        arrow_right = Arrow(
            start=RIGHT * 2 + DOWN * 0.5,
            end=RIGHT * 5,
            color=YELLOW
        )
        label_right = Text("斜面底角 θ", font_size=20, color=YELLOW).next_to(arrow_right, RIGHT)

        # 左上角（顶点）
        dot_top = Dot(point=UP * 6, color=BLUE, radius=0.08)
        arrow_top = Arrow(
            start=LEFT * 0.5 + UP * 2,
            end=UP * 5,
            color=BLUE
        )
        label_top = Text("顶点", font_size=20, color=BLUE).next_to(arrow_top, UP)

        # 标题
        title = Text("斜面几何结构（放大2倍）", font_size=32).to_edge(UP)

        self.add(title)
        self.play(Create(plane), run_time=1)
        self.play(
            Create(dot_left), Create(arrow_left), Write(label_left),
            Create(dot_right), Create(arrow_right), Write(label_right),
            Create(dot_top), Create(arrow_top), Write(label_top),
        )
        self.wait(3)


class TestInclinedPlaneGeometry(Scene):
    """
    几何演示：解释斜面的结构
    """

    def construct(self):
        title = Text("斜面的几何结构", font_size=36).to_edge(UP)
        self.add(title)

        # 创建斜面
        plane = InclinedPlane(angle=30, length=6.0)
        plane.center().shift(DOWN * 0.5)

        # 标注底边长度
        length_label = MathTex(r"L", font_size=28, color=WHITE)
        length_label.next_to(plane, DOWN, buff=0.3)

        # 标注高度
        height_label = MathTex(r"h = L \cdot \tan(\theta)", font_size=28, color=WHITE)
        height_label.next_to(plane, LEFT, buff=0.3).shift(UP * 0.5)

        # 说明文字
        explanations = VGroup(
            Text("• 左下角：直角 (90°)", font_size=20, color=GREEN),
            Text("• 右下角：斜面底角 θ", font_size=20, color=YELLOW),
            Text("• 左上角：顶点", font_size=20, color=BLUE),
            Text("• 底边长度：L", font_size=20, color=WHITE),
            Text("• 高度：h = L·tan(θ)", font_size=20, color=WHITE),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        explanations.to_edge(RIGHT).shift(LEFT * 1.0)

        self.play(Create(plane), run_time=1)
        self.play(Write(length_label), Write(height_label))
        self.play(FadeIn(explanations, shift=RIGHT * 0.5))
        self.wait(3)
