"""
物理力学组件库 - 轮播展示

每次只展示一个组件，清晰查看细节
按照类别顺序轮播展示所有18种组件
"""

from manim import *
import sys
import os

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from components.physics.mechanics import (
    # 1. 基础环境
    Wall,
    InclinedPlane,
    # 2. 刚体与物体
    Block,
    Cart,
    Weight,
    # 3. 连接装置
    Pulley,
    FixedPulley,
    MovablePulley,
    Rope,
    Spring,
    Rod,
    Hinge,
    # 4. 复杂轨道与槽车
    CircularGroove,
    SemicircleGroove,
    QuarterCircleGroove,
    SemicircleCart,
    QuarterCart,
    # 5. 测量工具
    SpringScale
)


class TestCarousel(Scene):
    """
    轮播展示：每次只显示一个组件

    流程：FadeIn -> wait(1) -> FadeOut -> 下一个
    """

    def construct(self):
        # ============================================
        # 标题
        # ============================================
        title = Text("物理力学组件库 - 轮播展示", font_size=42).to_edge(UP)
        self.add(title)

        # ============================================
        # 组件清单（按类别排序）
        # ============================================
        components_list = [
            # 1. 基础环境 (2种)
            (Wall(length=3.0), "Wall", "墙面/地面"),
            (InclinedPlane(angle=30, length=2.5), "InclinedPlane", "斜面"),

            # 2. 刚体与物体 (3种)
            (Block(width=1.5, height=1.0), "Block", "滑块"),
            (Cart(width=2.5, height=0.8), "Cart", "小车"),
            (Weight(width=0.9, height=1.3), "Weight", "钩码/砝码"),

            # 3. 连接装置 (7种)
            (Pulley(radius=0.6), "Pulley", "滑轮(基类)"),
            (FixedPulley(radius=0.6), "FixedPulley", "定滑轮"),
            (MovablePulley(radius=0.6), "MovablePulley", "动滑轮"),
            (Rope(length=4.0), "Rope", "绳"),
            (Spring(length=4.0), "Spring", "弹簧"),
            (Rod(length=4.0), "Rod", "杆"),
            (Hinge(radius=0.35), "Hinge", "铰链"),

            # 4. 复杂轨道与槽车 (5种)
            (CircularGroove(radius=1.5, groove_width=0.3), "CircularGroove", "圆槽"),
            (SemicircleGroove(radius=1.5, groove_width=0.3), "SemicircleGroove", "半圆槽"),
            (QuarterCircleGroove(radius=1.5, groove_width=0.3), "QuarterCircleGroove", "1/4圆槽"),
            (SemicircleCart(height=1.5), "SemicircleCart", "半圆槽车"),
            (QuarterCart(side_length=1.8), "QuarterCart", "1/4圆槽车"),

            # 5. 测量工具 (1种)
            (SpringScale(width=1.0, height=2.5), "SpringScale", "弹簧测力器"),
        ]

        # ============================================
        # 轮播展示每个组件
        # ============================================
        for i, (component, english_name, chinese_name) in enumerate(components_list):
            # 显示当前进度
            if hasattr(self, 'progress_text'):
                self.remove(self.progress_text)

            progress_text = Text(
                f"[{i+1}/{len(components_list)}]",
                font_size=24,
                color=GRAY
            ).to_edge(LEFT)
            self.progress_text = progress_text
            self.add(progress_text)

            # 展示组件
            self._show_component(component, english_name, chinese_name)

    def _show_component(self, component: VGroup, english: str, chinese: str):
        """
        展示单个组件

        Args:
            component: 组件对象
            english: 英文类名
            chinese: 中文名称
        """
        # 确保组件居中
        component.center()

        # 创建标签
        label = Text(
            f"{english} ({chinese})",
            font_size=28,
            color=YELLOW
        )
        label.next_to(component, DOWN, buff=0.8)

        # 创建组合
        display_group = VGroup(component, label)

        # FadeIn 动画
        self.play(FadeIn(display_group, shift=UP * 0.5), run_time=0.8)

        # 停留 1 秒
        self.wait(1)

        # FadeOut 动画
        self.play(FadeOut(display_group, shift=DOWN * 0.5), run_time=0.6)


class TestCarouselByCategory(Scene):
    """
    按类别轮播：每类组件展示前添加类别标题
    """

    def construct(self):
        title = Text("物理力学组件库 - 分类轮播", font_size=42).to_edge(UP)
        self.add(title)

        # ============================================
        # 按类别组织组件
        # ============================================
        categories = [
            {
                "name": "① 基础环境 (2种)",
                "components": [
                    (Wall(length=3.5), "Wall", "墙面/地面"),
                    (InclinedPlane(angle=30, length=3.0), "InclinedPlane", "斜面"),
                ]
            },
            {
                "name": "② 刚体与物体 (3种)",
                "components": [
                    (Block(width=1.8, height=1.2), "Block", "滑块"),
                    (Cart(width=3.0, height=1.0), "Cart", "小车"),
                    (Weight(width=1.0, height=1.5), "Weight", "钩码/砝码"),
                ]
            },
            {
                "name": "③ 连接装置 (7种)",
                "components": [
                    (Pulley(radius=0.7), "Pulley", "滑轮"),
                    (FixedPulley(radius=0.7), "FixedPulley", "定滑轮"),
                    (MovablePulley(radius=0.7), "MovablePulley", "动滑轮"),
                    (Rope(length=5.0), "Rope", "绳"),
                    (Spring(length=5.0), "Spring", "弹簧"),
                    (Rod(length=5.0), "Rod", "杆"),
                    (Hinge(size=0.8), "Hinge", "铰链"),
                ]
            },
            {
                "name": "④ 复杂轨道与槽车 (5种)",
                "components": [
                    (CircularGroove(radius=1.8), "CircularGroove", "圆槽"),
                    (SemicircleGroove(radius=1.8), "SemicircleGroove", "半圆槽"),
                    (QuarterCircleGroove(radius=1.8), "QuarterCircleGroove", "1/4圆槽"),
                    (SemicircleCart(width=3.0, height=1.2), "SemicircleCart", "半圆槽车"),
                    (QuarterCart(width=3.0, height=2.0), "QuarterCart", "1/4圆槽车"),
                ]
            },
            {
                "name": "⑤ 测量工具 (1种)",
                "components": [
                    (SpringScale(width=1.2, height=3.0), "SpringScale", "弹簧测力器"),
                ]
            },
        ]

        # ============================================
        # 按类别轮播展示
        # ============================================
        total_components = sum(len(cat["components"]) for cat in categories)
        shown_count = 0

        for category in categories:
            # 显示类别标题
            cat_title = Text(
                category["name"],
                font_size=32,
                color=BLUE
            ).to_edge(UP).shift(DOWN * 1.5)

            self.play(Write(cat_title), run_time=0.5)
            self.wait(0.3)

            # 展示该类别的所有组件
            for component, english, chinese in category["components"]:
                shown_count += 1

                # 更新进度
                if hasattr(self, 'progress_text'):
                    self.remove(self.progress_text)

                progress_text = Text(
                    f"[{shown_count}/{total_components}]",
                    font_size=20,
                    color=GRAY
                ).to_edge(LEFT)
                self.progress_text = progress_text
                self.add(progress_text)

                # 展示组件
                self._show_component(component, english, chinese)

            # 移除类别标题
            self.play(FadeOut(cat_title), run_time=0.3)

    def _show_component(self, component: VGroup, english: str, chinese: str):
        """展示单个组件"""
        component.center()

        label = Text(
            f"{english} ({chinese})",
            font_size=28,
            color=YELLOW
        )
        label.next_to(component, DOWN, buff=0.8)

        display_group = VGroup(component, label)

        self.play(Create(display_group), run_time=0.8)
        self.wait(1.2)
        self.play(FadeOut(display_group), run_time=0.5)


class TestSlowCarousel(Scene):
    """
    慢速轮播：每个组件停留更长时间，方便仔细观察
    """

    def construct(self):
        title = Text("物理力学组件库 - 慢速展示", font_size=42).to_edge(UP)
        self.add(title)

        components_list = [
            (Wall(length=4.0), "Wall", "墙面/地面"),
            (InclinedPlane(angle=30, length=3.0), "InclinedPlane", "斜面"),
            (Block(width=2.0, height=1.3), "Block", "滑块"),
            (Cart(width=3.0, height=1.0), "Cart", "小车"),
            (Weight(width=1.0, height=1.5), "Weight", "钩码/砝码"),
            (Pulley(radius=0.7), "Pulley", "滑轮(基类)"),
            (FixedPulley(radius=0.7), "FixedPulley", "定滑轮"),
            (MovablePulley(radius=0.7), "MovablePulley", "动滑轮"),
            (Rope(length=5.0), "Rope", "绳"),
            (Spring(length=5.0), "Spring", "弹簧"),
            (Rod(length=5.0), "Rod", "杆"),
            (Hinge(size=0.8), "Hinge", "铰链"),
            (CircularGroove(radius=2.0), "CircularGroove", "圆槽"),
            (SemicircleGroove(radius=2.0), "SemicircleGroove", "半圆槽"),
            (QuarterCircleGroove(radius=2.0), "QuarterCircleGroove", "1/4圆槽"),
            (SemicircleCart(width=3.0, height=1.2), "SemicircleCart", "半圆槽车"),
            (QuarterCart(width=3.0, height=2.0), "QuarterCart", "1/4圆槽车"),
            (SpringScale(width=1.2, height=3.0), "SpringScale", "弹簧测力器"),
        ]

        for i, (component, english, chinese) in enumerate(components_list):
            # 进度显示
            if hasattr(self, 'progress_text'):
                self.remove(self.progress_text)

            progress_text = Text(
                f"[{i+1}/{len(components_list)}]",
                font_size=24,
                color=GRAY
            ).to_edge(LEFT)
            self.progress_text = progress_text
            self.add(progress_text)

            # 组件居中
            component.center()

            # 标签
            label = Text(
                f"{english} ({chinese})",
                font_size=32,
                color=YELLOW
            )
            label.next_to(component, DOWN, buff=1.0)

            display_group = VGroup(component, label)

            # 更慢的动画，更长的停留时间
            self.play(Create(display_group), run_time=1.0)
            self.wait(2.0)  # 停留2秒
            self.play(FadeOut(display_group), run_time=0.6)


class TestQuickCarousel(Scene):
    """
    快速轮播：适合快速预览所有组件
    """

    def construct(self):
        components_list = [
            (Wall(length=3.0), "Wall", "墙面"),
            (InclinedPlane(angle=30, length=2.5), "InclinedPlane", "斜面"),
            (Block(width=1.5, height=1.0), "Block", "滑块"),
            (Cart(width=2.5, height=0.8), "Cart", "小车"),
            (Weight(width=0.9, height=1.3), "Weight", "钩码"),
            (Pulley(radius=0.6), "Pulley", "滑轮"),
            (FixedPulley(radius=0.6), "FixedPulley", "定滑轮"),
            (MovablePulley(radius=0.6), "MovablePulley", "动滑轮"),
            (Rope(length=4.0), "Rope", "绳"),
            (Spring(length=4.0), "Spring", "弹簧"),
            (Rod(length=4.0), "Rod", "杆"),
            (Hinge(radius=0.35), "Hinge", "铰链"),
            (CircularGroove(radius=1.5), "CircularGroove", "圆槽"),
            (SemicircleGroove(radius=1.5), "SemicircleGroove", "半圆槽"),
            (QuarterCircleGroove(radius=1.5), "QuarterCircleGroove", "1/4圆槽"),
            (SemicircleCart(width=2.5), "SemicircleCart", "半圆槽车"),
            (QuarterCart(width=2.5), "QuarterCart", "1/4圆槽车"),
            (SpringScale(width=1.0, height=2.5), "SpringScale", "弹簧测力器"),
        ]

        for component, english, chinese in components_list:
            component.center()

            label = Text(
                f"{english} ({chinese})",
                font_size=24,
                color=YELLOW
            )
            label.next_to(component, DOWN, buff=0.6)

            display_group = VGroup(component, label)

            self.play(FadeIn(display_group), run_time=0.4)
            self.wait(0.8)  # 快速预览，只停留0.8秒
            self.play(FadeOut(display_group), run_time=0.3)
