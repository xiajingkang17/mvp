"""
标准直线组件 - Standard Line Component

展示直线的五种方程形式：
1. 一般式: Ax + By + C = 0
2. 斜截式: y = kx + b
3. 点斜式: y - y1 = k(x - x1)
4. 两点式: (y - y1)/(y2 - y1) = (x - x1)/(x2 - x1)
5. 截距式: x/a + y/b = 1
"""

from manim import *
import numpy as np


class StandardLine(VGroup):
    """
    标准直线组件

    Parameters:
    -----------
    point1 : list or np.array
        第一个点 [x, y]
    point2 : list or np.array
        第二个点 [x, y]
    length : float
        线段显示长度
    show_equations : bool
        是否显示方程面板
    show_intercepts : bool
        是否显示截距点标记
    color : str
        直线颜色
    stroke_width : float
        线宽
    """

    def __init__(
        self,
        point1: list = None,
        point2: list = None,
        length: float = 10.0,
        show_equations: bool = True,
        show_intercepts: bool = True,
        color: str = WHITE,
        stroke_width: float = 4.0,
        **kwargs
    ):
        super().__init__(**kwargs)

        # 处理点的坐标
        if point1 is None:
            point1 = [0, 0, 0]
        if point2 is None:
            point2 = [length, 0, 0]

        self.p1 = np.array(point1, dtype=float)
        if len(self.p1) == 2:
            self.p1 = np.array([point1[0], point1[1], 0.0], dtype=float)

        self.p2 = np.array(point2, dtype=float)
        if len(self.p2) == 2:
            self.p2 = np.array([point2[0], point2[1], 0.0], dtype=float)

        self.length = length
        self.color = color

        # 计算直线方向
        delta = self.p2 - self.p1
        direction_norm = np.linalg.norm(delta)

        if direction_norm < 0.001:
            direction = RIGHT
        else:
            direction = delta / direction_norm

        # 判断直线类型
        self.is_vertical = abs(delta[0]) < 0.001
        self.is_horizontal = abs(delta[1]) < 0.001
        self.is_through_origin = np.allclose(self.p1, [0, 0, 0], atol=0.001)

        # 计算斜率和截距
        self.slope = 0.0
        self.y_intercept = 0.0

        if not self.is_vertical:
            if abs(delta[0]) > 0.001:
                self.slope = delta[1] / delta[0]
                # 计算y截距: y = kx + b => b = y - kx
                self.y_intercept = self.p1[1] - self.slope * self.p1[0]

        # 计算一般式系数 Ax + By + C = 0
        if self.is_vertical:
            self.A = 1.0
            self.B = 0.0
            self.C = -self.p1[0]
        elif self.is_horizontal:
            self.A = 0.0
            self.B = 1.0
            self.C = -self.p1[1]
        else:
            # y = kx + b => kx - y + b = 0
            self.A = self.slope
            self.B = -1.0
            self.C = self.y_intercept

        # 计算截距
        self.x_intercept = None
        self.y_intercept_point = None

        if abs(self.B) > 0.001:
            # y截距: x=0 => By + C = 0 => y = -C/B
            self.y_intercept_point = -self.C / self.B

        if abs(self.A) > 0.001:
            # x截距: y=0 => Ax + C = 0 => x = -C/A
            self.x_intercept = -self.C / self.A

        # 创建直线
        center = (self.p1 + self.p2) / 2
        actual_length = min(length, direction_norm)

        start = center - direction * (actual_length / 2)
        end = center + direction * (actual_length / 2)

        self.line = Line(start=start, end=end, color=color, stroke_width=stroke_width)
        self.add(self.line)

        # 添加端点
        self.add(Dot(self.p1, color=color, radius=0.06))
        self.add(Dot(self.p2, color=color, radius=0.06))

        # 添加截距标记
        if show_intercepts:
            intercepts = self._create_intercepts()
            self.add(intercepts)

        # 添加方程面板
        if show_equations:
            equations = self._create_equation_panel()
            self.add(equations)

    def _create_intercepts(self) -> VGroup:
        """创建截距标记"""
        group = VGroup()

        # X截距点
        if self.x_intercept is not None and abs(self.x_intercept) < 20:
            x_point = np.array([self.x_intercept, 0.0, 0.0])
            dot = Dot(x_point, color=YELLOW, radius=0.08)
            label = MathTex(rf"({self.x_intercept:.1f}, 0)", font_size=16, color=YELLOW)
            label.next_to(dot, DOWN + RIGHT, buff=0.1)
            group.add(dot, label)

        # Y截距点
        if self.y_intercept_point is not None and abs(self.y_intercept_point) < 20:
            y_point = np.array([0.0, self.y_intercept_point, 0.0])
            dot = Dot(y_point, color=YELLOW, radius=0.08)
            label = MathTex(rf"(0, {self.y_intercept_point:.1f})", font_size=16, color=YELLOW)
            label.next_to(dot, UP + RIGHT, buff=0.1)
            group.add(dot, label)

        return group

    def _create_equation_panel(self) -> VGroup:
        """创建方程面板"""
        panel = VGroup()
        panel.scale(0.6)

        y_offset = 0.0
        line_height = 0.5

        # 1. 一般式 Ax + By + C = 0
        a_str = f"{self.A:.2f}"
        b_str = f"{self.B:.2f}"
        c_str = f"{self.C:.2f}"

        # 简化显示
        if abs(self.A - 1.0) < 0.01:
            a_str = "1"
        elif abs(self.A + 1.0) < 0.01:
            a_str = "-1"
        elif abs(self.A) < 0.01:
            a_str = "0"

        if abs(self.B - 1.0) < 0.01:
            b_str = "1"
        elif abs(self.B + 1.0) < 0.01:
            b_str = "-1"
        elif abs(self.B) < 0.01:
            b_str = "0"

        if abs(self.C) < 0.01:
            c_str = "0"

        # 使用英文标签避免LaTeX中文问题
        gen_eq = MathTex(
            r"\text{General: }",
            a_str + "x",
            "+" if self.B >= 0 else "-",
            b_str + "y",
            "+" if self.C >= 0 else "-",
            c_str + " = 0",
            font_size=20,
            color=self.color
        )
        gen_eq.shift(UP * 3.5 + LEFT * 4)
        panel.add(gen_eq)

        # 2. 斜截式 y = kx + b (非垂直线)
        if not self.is_vertical and abs(self.slope) < 100:
            k_str = f"{self.slope:.2f}"
            b_str = f"{self.y_intercept:.2f}"

            if abs(self.slope - round(self.slope)) < 0.01:
                k_str = str(int(round(self.slope)))

            if abs(self.y_intercept - round(self.y_intercept)) < 0.01:
                b_str = str(int(round(self.y_intercept)))

            sign = "+" if self.y_intercept >= 0 else "-"

            slope_eq = MathTex(
                r"\text{Slope-Intercept: } y = ",
                k_str + "x",
                sign,
                b_str,
                font_size=20,
                color=YELLOW
            )
            slope_eq.next_to(gen_eq, DOWN, buff=line_height)
            panel.add(slope_eq)
            y_offset += line_height

        # 3. 点斜式 y - y1 = k(x - x1) (非垂直线)
        if not self.is_vertical and abs(self.slope) < 100:
            x1_str = str(int(round(self.p1[0]))) if abs(self.p1[0] - round(self.p1[0])) < 0.01 else f"{self.p1[0]:.1f}"
            y1_str = str(int(round(self.p1[1]))) if abs(self.p1[1] - round(self.p1[1])) < 0.01 else f"{self.p1[1]:.1f}"

            k_str = f"{self.slope:.2f}"
            if abs(self.slope - round(self.slope)) < 0.01:
                k_str = str(int(round(self.slope)))

            point_eq = MathTex(
                r"\text{Point-Slope: } y - " + y1_str + r" = " + k_str + r"(x - " + x1_str + r")",
                font_size=20,
                color=GREEN
            )
            point_eq.next_to(panel[-1], DOWN, buff=line_height)
            panel.add(point_eq)
            y_offset += line_height

        # 4. 两点式 (非垂直非水平)
        if not self.is_vertical and not self.is_horizontal:
            x1_str = str(int(round(self.p1[0]))) if abs(self.p1[0] - round(self.p1[0])) < 0.01 else f"{self.p1[0]:.1f}"
            y1_str = str(int(round(self.p1[1]))) if abs(self.p1[1] - round(self.p1[1])) < 0.01 else f"{self.p1[1]:.1f}"
            x2_str = str(int(round(self.p2[0]))) if abs(self.p2[0] - round(self.p2[0])) < 0.01 else f"{self.p2[0]:.1f}"
            y2_str = str(int(round(self.p2[1]))) if abs(self.p2[1] - round(self.p2[1])) < 0.01 else f"{self.p2[1]:.1f}"

            two_point_eq = MathTex(
                r"\text{Two-Point: }\frac{y-" + y1_str + r"}{" + y2_str + r"-" + y1_str + r"}",
                r" = ",
                r"\frac{x-" + x1_str + r"}{" + x2_str + r"-" + x1_str + r"}",
                font_size=18,
                color=BLUE
            )
            two_point_eq.next_to(panel[-1], DOWN, buff=line_height)
            panel.add(two_point_eq)
            y_offset += line_height

        # 5. 截距式 x/a + y/b = 1 (两个截距都存在且非零)
        if (self.x_intercept is not None and self.y_intercept_point is not None and
            abs(self.x_intercept) > 0.01 and abs(self.y_intercept_point) > 0.01 and
            abs(self.x_intercept) < 20 and abs(self.y_intercept_point) < 20):

            a_str = str(int(round(self.x_intercept))) if abs(self.x_intercept - round(self.x_intercept)) < 0.01 else f"{self.x_intercept:.1f}"
            b_str = str(int(round(self.y_intercept_point))) if abs(self.y_intercept_point - round(self.y_intercept_point)) < 0.01 else f"{self.y_intercept_point:.1f}"

            intercept_eq = MathTex(
                r"\text{Intercept: }\frac{x}{" + a_str + r"}",
                r" + ",
                r"\frac{y}{" + b_str + r"} = 1",
                font_size=20,
                color=PURPLE
            )
            intercept_eq.next_to(panel[-1], DOWN, buff=line_height)
            panel.add(intercept_eq)

        return panel
