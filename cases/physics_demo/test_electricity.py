"""
电学组件库 - 展示演示

简单展示各个电学组件，像"展示柜"一样排列
"""

from manim import *
import sys
import os

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from components.physics.electricity import (
    Resistor,
    Battery,
    Bulb,
    Switch,
    Capacitor
)


class TestElectricityComponents(Scene):
    """
    展示所有电学组件
    """

    def construct(self):
        # ============================================
        # 创建标题
        # ============================================
        title = Text("电学组件库", font_size=48).to_edge(UP)
        self.play(Write(title))
        self.wait(0.5)

        # ============================================
        # 创建组件展示柜
        # ============================================

        # 1. 电阻（新的长方形样式）
        resistor = Resistor(
            width=2.0,
            height=0.5,
            lead_length=0.8,
            color=WHITE,
            stroke_width=4.0
        )
        resistor_label = Text("Resistor (电阻)", font_size=24, color=BLUE)
        resistor_group = VGroup(resistor, resistor_label)
        resistor_group.arrange(DOWN, buff=0.3)

        # 2. 电池
        battery = Battery(
            width=1.5,
            height_long=1.2,
            height_short=0.6,
            color=WHITE,
            stroke_width=4.0,
            show_labels=True
        )
        battery_label = Text("Battery (电池)", font_size=24, color=RED)
        battery_group = VGroup(battery, battery_label)
        battery_group.arrange(DOWN, buff=0.3)

        # 3. 灯泡
        bulb = Bulb(
            radius=0.6,
            color=WHITE,
            stroke_width=4.0,
            fill_color=YELLOW,
            fill_opacity=0.3
        )
        bulb_label = Text("Bulb (灯泡)", font_size=24, color=YELLOW)
        bulb_group = VGroup(bulb, bulb_label)
        bulb_group.arrange(DOWN, buff=0.3)

        # 4. 开关
        switch = Switch(
            width=2.0,
            height=0.8,
            color=WHITE,
            stroke_width=4.0
        )
        switch_label = Text("Switch (开关)", font_size=24, color=GREEN)
        switch_group = VGroup(switch, switch_label)
        switch_group.arrange(DOWN, buff=0.3)

        # 5. 电容（额外赠送）
        capacitor = Capacitor(
            width=1.2,
            height=0.8,
            color=WHITE,
            stroke_width=4.0
        )
        capacitor_label = Text("Capacitor (电容)", font_size=24, color=PURPLE)
        capacitor_group = VGroup(capacitor, capacitor_label)
        capacitor_group.arrange(DOWN, buff=0.3)

        # ============================================
        # 排列所有组件（一字排开）
        # ============================================

        # 创建水平排列
        all_components = VGroup(
            resistor_group,
            battery_group,
            bulb_group,
            switch_group,
            capacitor_group
        )

        # 计算每个组件的间距，使它们均匀分布在屏幕上
        # 屏幕宽度约 14 单位，5 个组件，每个间隔约 3 单位
        all_components.arrange(RIGHT, buff=1.0)

        # 将整体移到屏幕中央
        all_components.shift(DOWN * 0.5)

        # ============================================
        # 依次显示每个组件
        # ============================================

        for group in all_components:
            self.play(Create(group), run_time=0.8)
            self.wait(0.3)

        # ============================================
        # 添加说明文字
        # ============================================
        description = Text(
            "基础电学元件符号（中国教材样式）",
            font_size=28,
            color=GRAY
        ).to_edge(DOWN)

        self.play(FadeIn(description), run_time=1)
        self.wait(2)

        # ============================================
        # 结束：淡出所有内容
        # ============================================
        self.play(
            FadeOut(VGroup(title, all_components, description)),
            run_time=1.5
        )


class TestSingleComponent(Scene):
    """
    单独展示电阻组件（示例）
    """

    def construct(self):
        # 创建大尺寸的电阻（长方形样式）
        resistor = Resistor(
            width=3.0,
            height=0.8,
            lead_length=1.0,
            color=YELLOW,
            stroke_width=6.0
        )

        # 居中显示
        resistor.center()

        # 添加标签
        label = Text("电阻符号（中国教材）", font_size=36).next_to(resistor, DOWN, buff=1.0)

        # 添加说明
        description = Text(
            "长方形框样式，黑色填充可遮挡背景线条",
            font_size=24,
            color=GRAY
        ).next_to(label, DOWN, buff=0.5)

        self.play(Create(resistor), run_time=2)
        self.play(Write(label), Write(description))
        self.wait(3)


class TestSimpleShowcase(Scene):
    """
    最简单的展示（快速测试用）
    """

    def construct(self):
        # 创建4个基础组件
        resistor = Resistor()
        battery = Battery()
        bulb = Bulb()
        switch = Switch()

        # 添加标签
        labels = VGroup(
            Text("Resistor", font_size=20),
            Text("Battery", font_size=20),
            Text("Bulb", font_size=20),
            Text("Switch", font_size=20)
        )

        # 组件和标签配对
        groups = [
            VGroup(resistor, labels[0]).arrange(DOWN, buff=0.3),
            VGroup(battery, labels[1]).arrange(DOWN, buff=0.3),
            VGroup(bulb, labels[2]).arrange(DOWN, buff=0.3),
            VGroup(switch, labels[3]).arrange(DOWN, buff=0.3)
        ]

        # 水平排列
        showcase = VGroup(*groups)
        showcase.arrange(RIGHT, buff=1.5)
        showcase.center()

        # 直接显示
        self.add(showcase)
        self.wait()
