"""
电学组件库 - 静态可视化组件

包含基本的电学元件：电阻、电池、灯泡、开关
所有组件都是纯静态展示，无复杂计算
"""

from __future__ import annotations

from manim import *
from typing import Optional


class Resistor(VGroup):
    """
    电阻组件（中国教材样式）

    绘制一个长方形框的电阻符号
    """

    def __init__(
        self,
        width: float = 2.0,
        height: float = 0.5,
        lead_length: float = 0.8,
        color: str = WHITE,
        stroke_width: float = 4.0,
        **kwargs
    ):
        super().__init__(**kwargs)

        # 长方形本体（电阻主体）
        # 使用黑色填充不透明，可以遮挡后面的线条
        resistor_body = Rectangle(
            width=width,
            height=height,
            stroke_color=color,      # 白色描边
            stroke_width=stroke_width,
            fill_color=BLACK,        # 黑色填充
            fill_opacity=1.0         # 完全不透明
        )

        # 左侧引线（从长方形左边中点向左）
        left_lead = Line(
            start=[-width/2 - lead_length, 0, 0],
            end=[-width/2, 0, 0],
            color=color,
            stroke_width=stroke_width
        )

        # 右侧引线（从长方形右边中点向右）
        right_lead = Line(
            start=[width/2, 0, 0],
            end=[width/2 + lead_length, 0, 0],
            color=color,
            stroke_width=stroke_width
        )

        # 组合所有部分
        self.add(left_lead, resistor_body, right_lead)


class Battery(VGroup):
    """
    电池组件

    绘制电池符号：长线（正极）和短线（负极）
    """

    def __init__(
        self,
        width: float = 1.5,
        height_long: float = 1.2,
        height_short: float = 0.6,
        color: str = WHITE,
        stroke_width: float = 4.0,
        show_labels: bool = True,
        **kwargs
    ):
        super().__init__(**kwargs)

        # 左侧长线（正极）
        positive_plate = Line(
            start=[-width/2, -height_long/2, 0],
            end=[-width/2, height_long/2, 0],
            color=color,
            stroke_width=stroke_width
        )

        # 右侧短线（负极）
        negative_plate = Line(
            start=[width/2, -height_short/2, 0],
            end=[width/2, height_short/2, 0],
            color=color,
            stroke_width=stroke_width
        )

        self.add(positive_plate, negative_plate)

        # 添加正负极标记
        if show_labels:
            plus_sign = Tex(
                r"+",
                font_size=48,
                color=color
            ).next_to(positive_plate, UP, buff=0.2)

            minus_sign = Tex(
                r"-",
                font_size=48,
                color=color
            ).next_to(negative_plate, UP, buff=0.2)

            self.add(plus_sign, minus_sign)


class Bulb(VGroup):
    """
    灯泡组件

    绘制一个圆圈，中间有交叉线
    """

    def __init__(
        self,
        radius: float = 0.6,
        color: str = WHITE,
        stroke_width: float = 4.0,
        fill_color: str = YELLOW,
        fill_opacity: float = 0.3,
        **kwargs
    ):
        super().__init__(**kwargs)

        # 外圆圈
        circle = Circle(
            radius=radius,
            color=color,
            stroke_width=stroke_width,
            fill_color=fill_color,
            fill_opacity=fill_opacity
        )

        # 中间的交叉线（X形状）
        # 左上到右下
        cross1 = Line(
            start=[-radius * 0.5, radius * 0.5, 0],
            end=[radius * 0.5, -radius * 0.5, 0],
            color=color,
            stroke_width=stroke_width
        )

        # 右上到左下
        cross2 = Line(
            start=[radius * 0.5, radius * 0.5, 0],
            end=[-radius * 0.5, -radius * 0.5, 0],
            color=color,
            stroke_width=stroke_width
        )

        self.add(circle, cross1, cross2)


class Switch(VGroup):
    """
    开关组件（断开状态）

    绘制一个断开的开关，像翘起的闸刀
    """

    def __init__(
        self,
        width: float = 2.0,
        height: float = 0.8,
        color: str = WHITE,
        stroke_width: float = 4.0,
        **kwargs
    ):
        super().__init__(**kwargs)

        # 左侧连接点（实心圆）
        left_terminal = Circle(
            radius=0.08,
            color=color,
            fill_color=color,
            fill_opacity=1.0
        ).shift([-width/2, 0, 0])

        # 左侧引线
        left_wire = Line(
            start=[-width/2, 0, 0],
            end=[-width/4, 0, 0],
            color=color,
            stroke_width=stroke_width
        )

        # 右侧引线
        right_wire = Line(
            start=[width/4, 0, 0],
            end=[width/2, 0, 0],
            color=color,
            stroke_width=stroke_width
        )

        # 右侧连接点（实心圆）
        right_terminal = Circle(
            radius=0.08,
            color=color,
            fill_color=color,
            fill_opacity=1.0
        ).shift([width/2, 0, 0])

        # 中间的闸刀（倾斜的线）
        lever = Line(
            start=[-width/4, 0, 0],
            end=[width/4, height, 0],  # 向上翘起
            color=color,
            stroke_width=stroke_width
        )

        self.add(left_wire, right_wire, lever, left_terminal, right_terminal)


class Capacitor(VGroup):
    """
    电容组件

    绘制两条平行的竖线
    """

    def __init__(
        self,
        width: float = 1.2,
        height: float = 0.8,
        color: str = WHITE,
        stroke_width: float = 4.0,
        **kwargs
    ):
        super().__init__(**kwargs)

        # 左侧极板
        left_plate = Line(
            start=[-width/2, -height/2, 0],
            end=[-width/2, height/2, 0],
            color=color,
            stroke_width=stroke_width
        )

        # 右侧极板
        right_plate = Line(
            start=[width/2, -height/2, 0],
            end=[width/2, height/2, 0],
            color=color,
            stroke_width=stroke_width
        )

        self.add(left_plate, right_plate)
