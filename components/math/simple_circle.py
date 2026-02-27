"""
简化版标准圆组件 (Simple Stable Implementation)

避免 ParametricFunction 和 Arc.shift() 问题
使用 Manim 原生 Circle 类
"""

from manim import *
import numpy as np


class StandardCircle(VGroup):
    """
    标准圆组件（简化版）

    自动展示圆的几何性质：
    - 圆曲线
    - 圆心（实心点）
    - 圆心坐标标签
    - 半径线（虚线）
    - 半径值标签
    """

    def __init__(
        self,
        radius: float = 2.0,
        center_point: list = None,
        show_center_dot: bool = True,
        show_center_coords: bool = True,
        show_radius_line: bool = True,
        show_radius_value: bool = True,
        color: str = WHITE,
        stroke_width: float = 4.0,
        point_radius: float = 0.08,
        **kwargs
    ):
        super().__init__(**kwargs)

        self.radius = radius

        # 处理圆心位置
        if center_point is None:
            center_point = np.array([0.0, 0.0, 0.0])
        else:
            center_point = np.array(center_point, dtype=float)

        self.center_point = center_point

        # ============================
        # 1. 创建圆（使用原生的 Circle）
        # ============================
        self.circle = Circle(radius=radius, color=color, stroke_width=stroke_width)
        self.add(self.circle)

        # ============================
        # 2. 创建圆心点（先在原点创建）
        # ============================
        if show_center_dot:
            self.dot = Dot(point=ORIGIN, radius=point_radius, color=YELLOW)
            self.add(self.dot)

        # ============================
        # 3. 创建圆心坐标标签（先在原点创建）
        # ============================
        if show_center_coords:
            # 格式化坐标值
            x_val = center_point[0]
            y_val = center_point[1]

            # 智能格式化：整数不显示小数点
            x_str = str(int(x_val)) if abs(x_val - round(x_val)) < 0.01 else f"{x_val:.1f}"
            y_str = str(int(y_val)) if abs(y_val - round(y_val)) < 0.01 else f"{y_val:.1f}"

            label_tex = rf"({x_str}, {y_str})"

            self.center_label = MathTex(label_tex, font_size=20, color=YELLOW)
            self.center_label.next_to(ORIGIN, UP + RIGHT, buff=0.1)
            self.add(self.center_label)

        # ============================
        # 4. 创建半径线（先在原点创建）
        # ============================
        if show_radius_line:
            # 计算 45 度方向的终点
            angle = 45 * DEGREES
            end_point = np.array([
                np.cos(angle) * radius,
                np.sin(angle) * radius,
                0.0
            ])

            self.radius_line = DashedLine(
                start=ORIGIN,
                end=end_point,
                color=color,
                stroke_width=stroke_width * 0.6,
                dash_length=0.15,
                dashed_ratio=0.5
            )
            self.add(self.radius_line)

            # ============================
            # 5. 创建半径值标签（先在原点创建）
            # ============================
            if show_radius_value:
                # 格式化半径值
                r_str = str(int(radius)) if abs(radius - round(radius)) < 0.01 else f"{radius:.1f}"

                self.radius_label = MathTex(rf"r={r_str}", font_size=20, color=color)

                # 放在半径线中点上方
                mid_point = end_point / 2
                self.radius_label.move_to(mid_point)
                self.radius_label.shift(UP * 0.3 + RIGHT * 0.2)
                self.add(self.radius_label)

        # ============================
        # 6. 核心：整体移动到目标位置
        # ============================
        # 不要在内部计算绝对坐标，而是让 VGroup 的 move_to 处理
        if not np.allclose(center_point, [0.0, 0.0, 0.0]):
            self.move_to(center_point)
