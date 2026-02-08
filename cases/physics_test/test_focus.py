"""
快速聚焦测试 - 只展示当前正在修改的组件

用途：在精修单个组件时，使用此脚本快速预览效果，无需渲染完整轮播
"""

from manim import *
import sys
import os

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from components.physics.mechanics import SpringScale, Pulley
from components.physics.electricity import Resistor
from components.physics.electromagnetism import Battery, Switch, Ammeter, Voltmeter, LightBulb, Capacitor, Rheostat, Potentiometer, Inductor, LED


class TestFocus(Scene):
    """
    快速聚焦测试：只展示单个组件

    使用方法：
    1. 修改下面的 component 变量为当前要测试的组件
    2. 运行：manim -pql cases/physics_test/test_focus.py TestFocus
    """

    def construct(self):
        # ============================================
        # 🔧 在这里修改要测试的组件
        # ============================================
        component = LED(
            side_length=1.2,         # 正三角形边长（增大）
            wire_length=0.8,         # 引线长度（增大）
            arrow_size=0.6,          # 发射箭头长度（增大）
            arrow_offset=(0.25, 0.15), # 箭头平移偏移量
            color=WHITE,
            stroke_width=4.0
        )

        component_name = "LED"
        component_chinese = "发光二极管（增大尺寸 + 平行箭头）"

        # ============================================
        # 展示组件
        # ============================================

        # 标题
        title = Text(
            f"{component_name} ({component_chinese})",
            font_size=36,
            color=YELLOW
        ).to_edge(UP)

        # 副标题（提示信息）
        hint = Text(
            "快速聚焦预览 - 单组件测试",
            font_size=20,
            color=GRAY
        ).next_to(title, DOWN, buff=0.3)

        # 确保组件居中
        component.center()

        # 创建展示组合
        display_group = VGroup(component, title, hint)

        # FadeIn 动画
        self.play(FadeIn(display_group, shift=UP * 0.5), run_time=0.8)

        # 长时间停留，方便观察细节
        self.wait(5)

        # FadeOut 动画
        self.play(FadeOut(display_group, shift=DOWN * 0.5), run_time=0.6)


class TestPulleyAngles(Scene):
    """
    测试 Pulley 不同角度的固定杆

    用于验证 rod_angle 参数是否正确工作
    """

    def construct(self):
        title = Text("Pulley 固定杆角度测试", font_size=36).to_edge(UP)
        self.add(title)

        # 创建5个不同角度的滑轮
        angles = [0, 45, 90, 135, 180]
        pulleys = VGroup()

        for i, angle in enumerate(angles):
            pulley = Pulley(
                radius=0.5,
                rod_angle=angle * DEGREES,
                color=WHITE
            )

            # 水平排列
            pulley.shift(LEFT * 3 + RIGHT * (i * 1.5))

            # 添加角度标签
            angle_label = Text(f"{angle}°", font_size=16).next_to(pulley, DOWN)
            pulleys.add(VGroup(pulley, angle_label))

        pulleys.center()

        self.play(FadeIn(pulleys))
        self.wait(5)


class TestSwitchAnimation(Scene):
    """
    测试 Switch 开关动画

    演示开关的闭合和断开动画
    """

    def construct(self):
        title = Text("开关动画测试", font_size=36).to_edge(UP)
        self.add(title)

        # 创建一个断开的开关
        switch = Switch(
            wire_length=0.8,
            switch_length=1.2,
            is_closed=False,  # 初始断开
            open_angle=30*DEGREES,
            color=WHITE,
            stroke_width=4.0
        )

        # 添加状态标签
        state_label = Text("状态：断开", font_size=24, color=RED).next_to(switch, DOWN, buff=0.5)

        # 居中显示
        switch_group = VGroup(switch, state_label)
        switch_group.center()

        self.play(FadeIn(switch_group))
        self.wait(1)

        # 演示闭合动画
        self.play(
            switch.close(),
            run_time=1.0,
            rate_func=smooth
        )
        state_label.text = "状态：闭合"
        state_label.color = GREEN
        self.wait(1.5)

        # 演示断开动画
        self.play(
            switch.open(),
            run_time=1.0,
            rate_func=smooth
        )
        state_label.text = "状态：断开"
        state_label.color = RED
        self.wait(1.5)

        # 再次闭合
        self.play(
            switch.close(),
            run_time=1.0,
            rate_func=smooth
        )
        state_label.text = "状态：闭合"
        state_label.color = GREEN
        self.wait(2)

        self.play(FadeOut(switch_group))


class TestRheostatAnimation(Scene):
    """
    测试 Rheostat 滑片移动动画

    演示滑片从左端移动到右端的动画
    """

    def construct(self):
        title = Text("滑动变阻器滑片测试", font_size=36).to_edge(UP)
        self.add(title)

        # 创建一个滑片在最左端的变阻器
        rheostat = Rheostat(
            body_width=2.0,
            body_height=0.5,
            handle_height=0.8,
            alpha=0.0,  # 初始在最左端
            wire_length=0.5,
            terminal_radius=0.08,
            color=WHITE,
            stroke_width=4.0
        )

        # 添加位置标签
        pos_label = Text("α = 0.0 (左端)", font_size=24, color=RED).next_to(rheostat, DOWN, buff=0.5)

        # 居中显示
        rheostat_group = VGroup(rheostat, pos_label)
        rheostat_group.center()

        self.play(FadeIn(rheostat_group))
        self.wait(1)

        # 演示滑片移动到中间
        self.wait(0.5)
        rheostat.change_value(0.5)  # 移动到中间
        pos_label.text = "α = 0.5 (居中)"
        self.wait(1.5)

        # 演示滑片移动到右端
        self.wait(0.5)
        rheostat.change_value(1.0)  # 移动到右端
        pos_label.text = "α = 1.0 (右端)"
        pos_label.color = BLUE
        self.wait(1.5)

        # 回到中间
        self.wait(0.5)
        rheostat.change_value(0.5)
        pos_label.text = "α = 0.5 (居中)"
        pos_label.color = YELLOW
        self.wait(1.5)

        # 回到左端
        self.wait(0.5)
        rheostat.change_value(0.0)
        pos_label.text = "α = 0.0 (左端)"
        pos_label.color = RED
        self.wait(2)

        self.play(FadeOut(rheostat_group))

