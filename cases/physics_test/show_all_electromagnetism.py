"""
电磁学组件库完整展示
展示所有 10 个电磁学组件
"""

from manim import *
import sys
import os

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from components.physics.electromagnetism import *


class ShowAllElectromagnetism(Scene):
    """
    完整展示所有电磁学组件

    使用方法：
    manim -pql cases/physics_test/show_all_electromagnetism.py ShowAllElectromagnetism
    """

    def construct(self):
        # 标题
        title = Text(
            "电磁学组件库 Electromagnetism Components",
            font_size=36,
            color=YELLOW
        ).to_edge(UP)

        subtitle = Text(
            "10 个组件 | 中国高中教材标准",
            font_size=24,
            color=GRAY
        ).next_to(title, DOWN, buff=0.3)

        self.add(title)
        self.add(subtitle)

        # 创建所有组件
        components = VGroup()

        # 第一行：基础元件
        row1 = self.create_row([
            (Battery(), "Battery\n直流电源"),
            (Capacitor(), "Capacitor\n电容器"),
            (Switch(is_closed=False), "Switch\n开关"),
            (Inductor(), "Inductor\n电感器"),
        ], start_y=2.0)

        # 第二行：测量仪表
        row2 = self.create_row([
            (Ammeter(), "Ammeter\n电流表"),
            (Voltmeter(), "Voltmeter\n电压表"),
            (LightBulb(), "LightBulb\n小灯泡"),
            (LED(), "LED\n发光二极管"),
        ], start_y=0.0)

        # 第三行：可变电阻
        row3 = self.create_row([
            (Rheostat(alpha=0.5), "Rheostat\n滑动变阻器"),
            (Potentiometer(), "Potentiometer\n电位器"),
        ], start_y=-2.0)

        # 组合所有行
        all_rows = VGroup(row1, row2, row3)
        all_rows.center()

        # 添加组件和标签
        self.play(FadeIn(all_rows, shift=UP * 0.5), run_time=1.0)

        # 长时间展示
        self.wait(10)

    def create_row(self, items, start_y):
        """创建一行组件"""
        row = VGroup()
        n = len(items)

        for i, (component, label_text) in enumerate(items):
            # 组件
            component.scale(0.8)  # 稍微缩小以适应布局
            component_y = start_y

            # 计算水平位置
            x_spacing = 10 / n
            x = -5 + (i + 0.5) * x_spacing

            # 放置组件
            component.move_to([x, component_y, 0])

            # 创建标签
            label = Text(
                label_text,
                font_size=14,
                color=WHITE
            ).next_to(component, DOWN, buff=0.2)

            # 组合
            group = VGroup(component, label)
            row.add(group)

        return row


class QuickShowcase(Scene):
    """
    快速展示：每个组件单独展示

    使用方法：
    manim -pql cases/physics_test/show_all_electromagnetism.py QuickShowcase
    """

    def construct(self):
        components = [
            ("Battery", "直流电源", Battery()),
            ("Switch", "单刀单掷开关", Switch(is_closed=False)),
            ("Ammeter", "电流表", Ammeter()),
            ("Voltmeter", "电压表", Voltmeter()),
            ("LightBulb", "小灯泡", LightBulb()),
            ("Capacitor", "电容器", Capacitor()),
            ("Rheostat", "滑动变阻器", Rheostat(alpha=0.5)),
            ("Potentiometer", "电位器", Potentiometer()),
            ("Inductor", "电感器", Inductor()),
            ("LED", "发光二极管", LED()),
        ]

        for i, (name, chinese, component) in enumerate(components):
            # 清空场景
            self.clear()

            # 标题
            title = Text(
                f"{name} ({chinese})",
                font_size=36,
                color=YELLOW
            ).to_edge(UP)

            self.add(title)

            # 居中组件
            component.center()

            # 添加到场景
            self.play(FadeIn(component), run_time=0.5)
            self.wait(1)

            # 淡出
            self.play(FadeOut(component), run_time=0.3)


if __name__ == "__main__":
    print("电磁学组件库展示脚本")
    print("=" * 50)
    print("可用场景：")
    print("1. ShowAllElectromagnetism - 展示所有组件（网格布局）")
    print("2. QuickShowcase - 快速展示（逐个展示）")
    print("=" * 50)
