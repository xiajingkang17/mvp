"""
解析几何组件库 - Analytic Geometry Components Library

包含常用的解析几何图形组件，自动展示数学性质。

作者: Manim 数学组件库
日期: 2026-02-11
"""

from __future__ import annotations

import math
import numpy as np
from manim import *
from typing import Optional, List, Tuple


class StandardEllipse(VGroup):
    """
    标准椭圆组件

    自动展示椭圆的几何性质：
    - 椭圆曲线 (黑色细实线)
    - 两个焦点 (实心小黑点)
    - 四个顶点 (实心小黑点)
    - 两条准线 (可选，垂直虚线)

    数学公式：
    - 标准方程：x²/a² + y²/b² = 1
    - 焦距：c = √(a² - b²)
    - 焦点位置：F₁(-c, 0), F₂(c, 0)
    - 顶点位置：A₁(-a, 0), A₂(a, 0), B₁(0, -b), B₂(0, b)
    - 准线方程：x = ± a²/c
    """

    def __init__(
        self,
        a: float = 3.0,  # 半长轴
        b: float = 2.0,  # 半短轴
        show_foci: bool = True,  # 是否显示焦点
        show_vertices: bool = True,  # 是否显示顶点
        show_axes: bool = False,  # 是否显示长轴短轴虚线
        show_directrix: bool = False,  # 是否显示准线
        directrix_config: dict = None,  # 准线配置
        color: str = WHITE,
        stroke_width: float = 4.0,
        point_radius: float = 0.08,  # 焦点/顶点半径
        **kwargs
    ):
        super().__init__(**kwargs)

        # 验证参数：a >= b
        if a < b:
            raise ValueError(f"半长轴 a ({a}) 必须大于或等于半短轴 b ({b})")

        self.a = a
        self.b = b

        # 计算焦距 c = √(a² - b²)
        self.c = math.sqrt(a**2 - b**2)

        # 准线配置默认值
        if directrix_config is None:
            directrix_config = {}
        self.directrix_config = {
            'color': directrix_config.get('color', GRAY),
            'stroke_width': directrix_config.get('stroke_width', stroke_width * 0.6),
            'dash_length': directrix_config.get('dash_length', 0.15),
            'dashed_ratio': directrix_config.get('dashed_ratio', 0.5),
        }

        # 1. 绘制椭圆曲线
        ellipse = Ellipse(
            width=a * 2,  # 宽度 = 2a
            height=b * 2,  # 高度 = 2b
            color=color,
            stroke_width=stroke_width
        )
        ellipse.move_to(ORIGIN)
        self.add(ellipse)

        # 2. 绘制焦点 F₁, F₂
        if show_foci:
            f1 = Dot(
                point=LEFT * self.c,
                radius=point_radius,
                color=color
            )
            f2 = Dot(
                point=RIGHT * self.c,
                radius=point_radius,
                color=color
            )
            self.f1 = f1
            self.f2 = f2
            self.add(f1, f2)

        # 3. 绘制四个顶点 A₁, A₂, B₁, B₂
        if show_vertices:
            a1 = Dot(
                point=LEFT * a,
                radius=point_radius,
                color=color
            )
            a2 = Dot(
                point=RIGHT * a,
                radius=point_radius,
                color=color
            )
            b1 = Dot(
                point=DOWN * b,
                radius=point_radius,
                color=color
            )
            b2 = Dot(
                point=UP * b,
                radius=point_radius,
                color=color
            )
            self.a1 = a1  # 左顶点
            self.a2 = a2  # 右顶点
            self.b1 = b1  # 下顶点
            self.b2 = b2  # 上顶点
            self.add(a1, a2, b1, b2)

        # 4. 绘制长轴和短轴虚线（可选）
        if show_axes:
            # 长轴（x轴方向，从 -a 到 a）
            major_axis = DashedLine(
                start=LEFT * a,
                end=RIGHT * a,
                color=color,
                stroke_width=stroke_width * 0.5,
                dash_length=0.2,
                dashed_ratio=0.5
            )

            # 短轴（y轴方向，从 -b 到 b）
            minor_axis = DashedLine(
                start=DOWN * b,
                end=UP * b,
                color=color,
                stroke_width=stroke_width * 0.5,
                dash_length=0.2,
                dashed_ratio=0.5
            )

            self.add(major_axis, minor_axis)

        # 5. 绘制准线（可选）
        if show_directrix:
            directrices = self._get_directrix()
            self.add(directrices)

    def _get_directrix(self) -> VGroup:
        """
        绘制椭圆的两条准线

        准线方程：x = ± a²/c
        返回包含两条垂直虚线的 VGroup
        """
        # 计算准线的 x 坐标
        directrix_x = self.a ** 2 / self.c

        # 左准线 (x = -a²/c)
        left_directrix = DashedLine(
            start=LEFT * directrix_x + UP * (self.b * 1.5),
            end=LEFT * directrix_x + DOWN * (self.b * 1.5),
            color=self.directrix_config['color'],
            stroke_width=self.directrix_config['stroke_width'],
            dash_length=self.directrix_config['dash_length'],
            dashed_ratio=self.directrix_config['dashed_ratio']
        )

        # 右准线 (x = +a²/c)
        right_directrix = DashedLine(
            start=RIGHT * directrix_x + UP * (self.b * 1.5),
            end=RIGHT * directrix_x + DOWN * (self.b * 1.5),
            color=self.directrix_config['color'],
            stroke_width=self.directrix_config['stroke_width'],
            dash_length=self.directrix_config['dash_length'],
            dashed_ratio=self.directrix_config['dashed_ratio']
        )

        return VGroup(left_directrix, right_directrix)


class StandardHyperbola(VGroup):
    """
    标准双曲线组件

    自动展示双曲线的几何性质：
    - 双曲线分支（左右两支）
    - 两个焦点
    - 两个顶点
    - 两条渐近线（可选）
    - 两条准线（可选）
    - 渐近线和准线的标签（可选）

    数学公式：
    - 标准方程：x²/a² - y²/b² = 1
    - 焦距：c = √(a² + b²)
    - 焦点位置：F₁(-c, 0), F₂(c, 0)
    - 顶点位置：A₁(-a, 0), A₂(a, 0)
    - 渐近线方程：y = ±(b/a)x
    - 准线方程：x = ± a²/c
    """

    def __init__(
        self,
        a: float = 3.0,
        b: float = 2.0,
        branch: str = "both",  # "left", "right", or "both"
        show_foci: bool = True,
        show_vertices: bool = True,
        show_asymptotes: bool = True,
        asymptote_labels: bool = False,
        show_directrices: bool = False,
        directrix_labels: bool = False,
        asymptote_config: dict = None,
        directrix_config: dict = None,
        color: str = BLUE,  # 双曲线建议用蓝色
        stroke_width: float = 4.0,
        point_radius: float = 0.08,
        **kwargs
    ):
        super().__init__(**kwargs)

        self.a = a
        self.b = b

        # 计算焦距 c = √(a² + b²)  (注意：双曲线是加号！)
        self.c = math.sqrt(a**2 + b**2)

        # 渐近线配置默认值
        if asymptote_config is None:
            asymptote_config = {}
        self.asymptote_config = {
            'color': asymptote_config.get('color', YELLOW),
            'stroke_width': asymptote_config.get('stroke_width', stroke_width * 0.6),
            'dash_length': asymptote_config.get('dash_length', 0.15),
            'dashed_ratio': asymptote_config.get('dashed_ratio', 0.5),
        }

        # 准线配置默认值
        if directrix_config is None:
            directrix_config = {}
        self.directrix_config = {
            'color': directrix_config.get('color', GRAY),
            'stroke_width': directrix_config.get('stroke_width', stroke_width * 0.6),
            'dash_length': directrix_config.get('dash_length', 0.12),
            'dashed_ratio': directrix_config.get('dashed_ratio', 0.5),
        }

        # ============================
        # 1. 绘制双曲线分支
        # ============================
        # 方程：x²/a² - y²/b² = 1
        # 参数方程：x = a*sec(t), y = b*tan(t)
        # 或直接解方程：y = ±b*sqrt(x²/a² - 1)

        if branch in ["left", "both"]:
            left_branch_upper = self._create_hyperbola_branch_upper(a, b, "left", color, stroke_width)
            left_branch_lower = self._create_hyperbola_branch_lower(a, b, "left", color, stroke_width)
            self.add(left_branch_upper, left_branch_lower)

        if branch in ["right", "both"]:
            right_branch_upper = self._create_hyperbola_branch_upper(a, b, "right", color, stroke_width)
            right_branch_lower = self._create_hyperbola_branch_lower(a, b, "right", color, stroke_width)
            self.add(right_branch_upper, right_branch_lower)

        # ============================
        # 2. 绘制焦点 F₁, F₂
        # ============================
        if show_foci:
            f1 = Dot(point=LEFT * self.c, radius=point_radius, color=YELLOW)  # 焦点用黄色区分
            f2 = Dot(point=RIGHT * self.c, radius=point_radius, color=YELLOW)
            self.f1 = f1
            self.f2 = f2
            self.add(f1, f2)

        # ============================
        # 3. 绘制顶点 A₁, A₂
        # ============================
        if show_vertices:
            v1 = Dot(point=LEFT * a, radius=point_radius, color=color)
            v2 = Dot(point=RIGHT * a, radius=point_radius, color=color)
            self.v1 = v1  # 左顶点
            self.v2 = v2  # 右顶点
            self.add(v1, v2)

        # ============================
        # 4. 绘制渐近线（可选）
        # ============================
        if show_asymptotes:
            asymptotes = self._get_asymptotes()
            self.add(asymptotes)

            # 添加渐近线标签（可选）
            if asymptote_labels:
                asymptote_label_group = self._get_asymptote_labels()
                self.add(asymptote_label_group)

        # ============================
        # 5. 绘制准线（可选）
        # ============================
        if show_directrices:
            directrices = self._get_directrices()
            self.add(directrices)

            # 添加准线标签（可选）
            if directrix_labels:
                directrix_label_group = self._get_directrix_labels()
                self.add(directrix_label_group)

    def _create_hyperbola_branch_upper(self, a: float, b: float, direction: str, color: str, stroke_width: float):
        """创建双曲线的上半支"""
        # 使用参数方程：x = a/cos(t), y = b*tan(t)
        points = []
        x_range = np.linspace(a, a + 4, 80)  # 从顶点开始，向右延伸

        for x in x_range:
            # y = b * sqrt(x²/a² - 1)
            y = b * math.sqrt(x**2 / a**2 - 1)
            if direction == "left":
                x = -x
            points.append([x, y, 0])

        curve = VMobject()
        curve.set_points_as_corners(points)
        curve.set_color(color)
        curve.set_stroke(width=stroke_width)
        curve.make_smooth()

        return curve

    def _create_hyperbola_branch_lower(self, a: float, b: float, direction: str, color: str, stroke_width: float):
        """创建双曲线的下半支"""
        points = []
        x_range = np.linspace(a, a + 4, 80)

        for x in x_range:
            y = -b * math.sqrt(x**2 / a**2 - 1)
            if direction == "left":
                x = -x
            points.append([x, y, 0])

        curve = VMobject()
        curve.set_points_as_corners(points)
        curve.set_color(color)
        curve.set_stroke(width=stroke_width)
        curve.make_smooth()

        return curve

    def _get_asymptotes(self) -> VGroup:
        """
        绘制双曲线的两条渐近线

        渐近线方程：y = ±(b/a)x
        返回包含四条虚线的 VGroup（从原点向四个方向延伸）
        """
        # 计算渐近线的终点坐标
        # 渐近线应该足够长，超出双曲线范围
        line_length = max(self.a, self.b) * 2.5

        # y = (b/a)x  （第一象限）
        line1_end = RIGHT * (line_length * self.a / math.sqrt(self.a**2 + self.b**2)) + \
                     UP * (line_length * self.b / math.sqrt(self.a**2 + self.b**2))

        # y = -(b/a)x  （第四象限）
        line2_end = RIGHT * (line_length * self.a / math.sqrt(self.a**2 + self.b**2)) + \
                     DOWN * (line_length * self.b / math.sqrt(self.a**2 + self.b**2))

        # y = (b/a)x  （第二象限）
        line3_end = LEFT * (line_length * self.a / math.sqrt(self.a**2 + self.b**2)) + \
                     UP * (line_length * self.b / math.sqrt(self.a**2 + self.b**2))

        # y = -(b/a)x  （第三象限）
        line4_end = LEFT * (line_length * self.a / math.sqrt(self.a**2 + self.b**2)) + \
                     DOWN * (line_length * self.b / math.sqrt(self.a**2 + self.b**2))

        line1 = DashedLine(
            start=ORIGIN,
            end=line1_end,
            color=self.asymptote_config['color'],
            stroke_width=self.asymptote_config['stroke_width'],
            dash_length=self.asymptote_config['dash_length'],
            dashed_ratio=self.asymptote_config['dashed_ratio']
        )

        line2 = DashedLine(
            start=ORIGIN,
            end=line2_end,
            color=self.asymptote_config['color'],
            stroke_width=self.asymptote_config['stroke_width'],
            dash_length=self.asymptote_config['dash_length'],
            dashed_ratio=self.asymptote_config['dashed_ratio']
        )

        line3 = DashedLine(
            start=ORIGIN,
            end=line3_end,
            color=self.asymptote_config['color'],
            stroke_width=self.asymptote_config['stroke_width'],
            dash_length=self.asymptote_config['dash_length'],
            dashed_ratio=self.asymptote_config['dashed_ratio']
        )

        line4 = DashedLine(
            start=ORIGIN,
            end=line4_end,
            color=self.asymptote_config['color'],
            stroke_width=self.asymptote_config['stroke_width'],
            dash_length=self.asymptote_config['dash_length'],
            dashed_ratio=self.asymptote_config['dashed_ratio']
        )

        return VGroup(line1, line2, line3, line4)

    def _get_asymptote_labels(self) -> VGroup:
        """
        添加渐近线标签

        标签位置在渐近线末端附近
        """
        line_length = max(self.a, self.b) * 2.0

        # 计算标签位置
        pos1 = RIGHT * (line_length * self.a / math.sqrt(self.a**2 + self.b**2)) * 1.1 + \
                UP * (line_length * self.b / math.sqrt(self.a**2 + self.b**2)) * 1.1

        pos2 = RIGHT * (line_length * self.a / math.sqrt(self.a**2 + self.b**2)) * 1.1 + \
                DOWN * (line_length * self.b / math.sqrt(self.a**2 + self.b**2)) * 1.1

        # 创建标签
        label1 = MathTex(r"y=\frac{b}{a}x", font_size=20, color=self.asymptote_config['color'])
        label1.move_to(pos1).shift(RIGHT * 0.3 + UP * 0.3)

        label2 = MathTex(r"y=-\frac{b}{a}x", font_size=20, color=self.asymptote_config['color'])
        label2.move_to(pos2).shift(RIGHT * 0.3 + DOWN * 0.3)

        return VGroup(label1, label2)

    def _get_directrices(self) -> VGroup:
        """
        绘制双曲线的两条准线

        准线方程：x = ± a²/c
        返回包含两条垂直虚线的 VGroup
        """
        # 计算准线的 x 坐标
        directrix_x = self.a ** 2 / self.c

        # 左准线 (x = -a²/c)
        left_directrix = DashedLine(
            start=LEFT * directrix_x + UP * (self.b * 2),
            end=LEFT * directrix_x + DOWN * (self.b * 2),
            color=self.directrix_config['color'],
            stroke_width=self.directrix_config['stroke_width'],
            dash_length=self.directrix_config['dash_length'],
            dashed_ratio=self.directrix_config['dashed_ratio']
        )

        # 右准线 (x = +a²/c)
        right_directrix = DashedLine(
            start=RIGHT * directrix_x + UP * (self.b * 2),
            end=RIGHT * directrix_x + DOWN * (self.b * 2),
            color=self.directrix_config['color'],
            stroke_width=self.directrix_config['stroke_width'],
            dash_length=self.directrix_config['dash_length'],
            dashed_ratio=self.directrix_config['dashed_ratio']
        )

        return VGroup(left_directrix, right_directrix)

    def _get_directrix_labels(self) -> VGroup:
        """
        添加准线标签

        标签位置在准线上方
        """
        directrix_x = self.a ** 2 / self.c

        # 左准线标签
        left_label = MathTex(r"x=-\frac{a^2}{c}", font_size=18, color=self.directrix_config['color'])
        left_label.move_to([-(directrix_x + 0.5), self.b * 1.5, 0])

        # 右准线标签
        right_label = MathTex(r"x=+\frac{a^2}{c}", font_size=18, color=self.directrix_config['color'])
        right_label.move_to([directrix_x + 0.5, self.b * 1.5, 0])

        return VGroup(left_label, right_label)


class StandardParabola(VGroup):
    """
    标准抛物线组件

    自动展示抛物线的几何性质：
    - 抛物线曲线
    - 焦点
    - 顶点（原点）
    - 准线（实线，非虚线）
    - 准线标签（可选）

    数学公式（标准形式）：
    - 开口向右：y² = 2px，焦点 (p/2, 0)，准线 x = -p/2
    - 开口向左：y² = -2px，焦点 (-p/2, 0)，准线 x = p/2
    - 开口向上：x² = 2py，焦点 (0, p/2)，准线 y = -p/2
    - 开口向下：x² = -2py，焦点 (0, -p/2)，准线 y = p/2
    """

    def __init__(
        self,
        p: float = 2.0,  # 焦准距（默认改为 2）
        direction: str = "RIGHT",  # "RIGHT", "LEFT", "UP", "DOWN"（大写）
        x_range: tuple = (-3, 3),  # 水平方向的绘制范围
        y_range: tuple = (-3, 3),  # 垂直方向的绘制范围
        show_vertex: bool = True,
        show_focus: bool = True,
        show_directrix: bool = True,  # 默认开启
        directrix_style: dict = None,  # 准线样式配置（默认实线）
        directrix_label: bool = False,  # 显示准线标签
        color: str = WHITE,
        stroke_width: float = 4.0,
        point_radius: float = 0.08,
        **kwargs
    ):
        super().__init__(**kwargs)

        self.p = p
        self.direction = direction.upper()  # 统一转大写
        self.x_range = x_range
        self.y_range = y_range

        # 准线样式配置（默认实线）
        if directrix_style is None:
            directrix_style = {}
        self.directrix_config = {
            'stroke_style': directrix_style.get('stroke_style', 'solid'),  # 默认实线
            'color': directrix_style.get('color', YELLOW),
            'stroke_width': directrix_style.get('stroke_width', stroke_width * 0.8),
            'dash_length': directrix_style.get('dash_length', 0.15),
        }

        # ============================
        # 计算焦点和准线位置
        # ============================
        # 根据方向动态计算
        focus_pos, directrix_pos, directrix_orientation = self._calculate_positions()

        # ============================
        # 1. 绘制抛物线曲线
        # ============================
        parabola = self._create_parabola_curve(color, stroke_width)
        self.add(parabola)

        # ============================
        # 2. 绘制焦点
        # ============================
        if show_focus:
            focus = Dot(
                point=focus_pos,
                radius=point_radius,
                color=YELLOW  # 焦点用黄色区分
            )
            self.focus = focus
            self.add(focus)

        # ============================
        # 3. 绘制顶点（原点）
        # ============================
        if show_vertex:
            vertex = Dot(
                point=ORIGIN,
                radius=point_radius * 0.8,  # 顶点稍小
                color=color
            )
            self.vertex = vertex
            self.add(vertex)

        # ============================
        # 4. 绘制准线（实线，非虚线）
        # ============================
        if show_directrix:
            directrix = self._create_directrix_line(directrix_pos, directrix_orientation)
            self.add(directrix)

            # 添加准线标签（可选）
            if directrix_label:
                label = self._get_directrix_label(directrix_pos, directrix_orientation)
                self.add(label)

    def _calculate_positions(self) -> tuple:
        """
        根据方向计算焦点和准线位置

        使用标准公式：y² = 2px 或 x² = 2py
        焦点在 p/2 处，准线在 -p/2 处

        返回：(焦点位置, 准线位置, 准线方向)
        """
        p_half = self.p / 2

        if self.direction == "RIGHT":
            # y² = 2px
            focus_pos = RIGHT * p_half
            directrix_pos = LEFT * p_half
            directrix_orientation = "vertical"
            equation = r"x=-\frac{p}{2}"

        elif self.direction == "LEFT":
            # y² = -2px
            focus_pos = LEFT * p_half
            directrix_pos = RIGHT * p_half
            directrix_orientation = "vertical"
            equation = r"x=+\frac{p}{2}"

        elif self.direction == "UP":
            # x² = 2py
            focus_pos = UP * p_half
            directrix_pos = DOWN * p_half
            directrix_orientation = "horizontal"
            equation = r"y=-\frac{p}{2}"

        elif self.direction == "DOWN":
            # x² = -2py
            focus_pos = DOWN * p_half
            directrix_pos = UP * p_half
            directrix_orientation = "horizontal"
            equation = r"y=+\frac{p}{2}"

        else:
            raise ValueError(f"Invalid direction: {self.direction}. Must be RIGHT, LEFT, UP, or DOWN")

        self.directrix_equation = equation  # 保存方程用于标签
        return focus_pos, directrix_pos, directrix_orientation

    def _create_parabola_curve(self, color: str, stroke_width: float) -> VMobject:
        """创建抛物线曲线"""
        points = []

        # 根据方向确定参数范围
        if self.direction in ["RIGHT", "LEFT"]:
            # y² = 2px，即 x = y²/(2p)
            # y 作为参数，y 范围使用 y_range
            t_range = np.linspace(self.y_range[0], self.y_range[1], 100)

            for t in t_range:
                x = t**2 / (2 * self.p)
                if self.direction == "LEFT":
                    x = -x
                points.append([x, t, 0])

        else:  # UP or DOWN
            # x² = 2py，即 y = x²/(2p)
            # x 作为参数，x 范围使用 x_range
            t_range = np.linspace(self.x_range[0], self.x_range[1], 100)

            for t in t_range:
                y = t**2 / (2 * self.p)
                if self.direction == "DOWN":
                    y = -y
                points.append([t, y, 0])

        # 创建平滑曲线
        curve = VMobject()
        curve.set_points_as_corners(points)
        curve.set_color(color)
        curve.set_stroke(width=stroke_width)
        curve.make_smooth()

        return curve

    def _create_directrix_line(self, position: np.ndarray, orientation: str) -> Line:
        """
        创建准线

        注意：用户明确要求默认使用实线，不是虚线！
        """
        # 计算准线的长度（需要足够长）
        line_length = 6

        if orientation == "vertical":
            # 垂直准线（用于 RIGHT/LEFT 方向）
            directrix = Line(
                start=position + UP * (line_length / 2),
                end=position + DOWN * (line_length / 2),
                color=self.directrix_config['color'],
                stroke_width=self.directrix_config['stroke_width']
            )
        else:  # horizontal
            # 水平准线（用于 UP/DOWN 方向）
            directrix = Line(
                start=position + LEFT * (line_length / 2),
                end=position + RIGHT * (line_length / 2),
                color=self.directrix_config['color'],
                stroke_width=self.directrix_config['stroke_width']
            )

        return directrix

    def _get_directrix_label(self, directrix_pos: np.ndarray, orientation: str) -> MathTex:
        """创建准线标签"""
        label = MathTex(
            self.directrix_equation,
            font_size=20,
            color=self.directrix_config['color']
        )

        # 根据准线方向调整标签位置
        if orientation == "vertical":
            # 垂直准线，标签放在上方或下方
            if self.direction == "RIGHT":
                # 准线在左侧，标签在上方
                label.move_to(directrix_pos + UP * 0.5 + LEFT * 0.3)
            else:  # LEFT
                # 准线在右侧，标签在上方
                label.move_to(directrix_pos + UP * 0.5 + RIGHT * 0.3)
        else:  # horizontal
            # 水平准线，标签放在左侧或右侧
            if self.direction == "UP":
                # 准线在下方，标签在左侧
                label.move_to(directrix_pos + LEFT * 0.5 + DOWN * 0.3)
            else:  # DOWN
                # 准线在上方，标签在左侧
                label.move_to(directrix_pos + LEFT * 0.5 + UP * 0.3)


class StandardCircle(VGroup):
    """
    标准圆组件

    自动展示圆的几何性质：
    - 圆曲线
    - 圆心（实心点）
    - 圆心坐标标签
    - 半径线（虚线）
    - 半径值标签

    数学公式：
    - 标准方程：(x - h)² + (y - k)² = r²
    - 其中 (h, k) 是圆心，r 是半径
    """

    def __init__(
        self,
        radius: float = 2.0,  # 半径
        center_point: list = None,  # 圆心位置（默认原点）
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

        # 保存圆心供内部使用
        self._center_point_local = center_point
        self.center_point = center_point  # 最终位置（用于外部访问）

        # 先创建所有元素（不立即添加到 self）
        elements_to_add = []

        # ============================
        # 1. 创建圆（使用 ParametricFunction 避免 Arc 问题）
        # ============================
        # 参数方程：x = center_x + r*cos(t), y = center_y + r*sin(t)

        def circle_func(t):
            return np.array([
                center_point[0] + radius * math.cos(t),
                center_point[1] + radius * math.sin(t),
                0.0
            ])

        circle = ParametricFunction(
            circle_func,
            t_range=[0, 2 * PI],
            color=color,
            stroke_width=stroke_width
        )

        self.circle = circle
        elements_to_add.append(circle)

        # ============================
        # 2. 绘制圆心（实心点）
        # ============================
        if show_center_dot:
            center_dot = Dot(
                point=center_point,
                radius=point_radius,
                color=YELLOW  # 圆心用黄色
            )
            self.center_dot = center_dot
            elements_to_add.append(center_dot)

        # ============================
        # 3. 显示圆心坐标标签
        # ============================
        if show_center_coords and show_center_dot:
            coord_label = self._create_coord_label()
            elements_to_add.append(coord_label)

        # ============================
        # 4. 绘制半径线（虚线）
        # ============================
        if show_radius_line:
            radius_line = self._create_radius_line(color, stroke_width)
            elements_to_add.append(radius_line)

            # ============================
            # 5. 显示半径值标签
            # ============================
            if show_radius_value:
                radius_label = self._create_radius_label(color)
                elements_to_add.append(radius_label)

        # 一次性添加所有元素
        for element in elements_to_add:
            self.add(element)

    def _create_coord_label(self) -> MathTex:
        """
        创建圆心坐标标签

        格式：(x, y)
        - 整数显示为整数：(2, 1)
        - 浮点数保留1位小数：(2.5, 1.0)
        """
        x = self._center_point_local[0]
        y = self._center_point_local[1]

        # 格式化坐标值
        if abs(x - round(x)) < 0.01:  # 接近整数
            x_str = str(int(round(x)))
        else:
            x_str = f"{x:.1f}"

        if abs(y - round(y)) < 0.01:
            y_str = str(int(round(y)))
        else:
            y_str = f"{y:.1f}"

        # 创建坐标标签
        coord_label = MathTex(
            rf"({x_str}, {y_str})",
            font_size=20,
            color=YELLOW
        )

        # 放置在圆心右上角（相对于局部圆心）
        coord_label.move_to(self._center_point_local + UP * 0.15 + RIGHT * 0.15)

        return coord_label

    def _create_radius_line(self, color: str, stroke_width: float) -> DashedLine:
        """
        创建半径线

        方向：从圆心指向右上方 45 度角（最美观）
        样式：虚线
        """
        # 计算 45 度方向的终点
        # 单位向量：(cos(45°), sin(45°))
        angle = 45 * DEGREES
        direction = np.array([math.cos(angle), math.sin(angle), 0])
        end_point = self._center_point_local + direction * self.radius

        radius_line = DashedLine(
            start=self._center_point_local,
            end=end_point,
            color=color,
            stroke_width=stroke_width * 0.6,
            dash_length=0.15,
            dashed_ratio=0.5
        )

        # 保存半径线终点供标签使用
        self.radius_line_end = end_point

        return radius_line

    def _create_radius_label(self, color: str) -> MathTex:
        """
        创建半径值标签

        格式：r = 2.0
        位置：在半径线中点上方
        """
        # 格式化半径值
        if abs(self.radius - round(self.radius)) < 0.01:
            radius_str = str(int(round(self.radius)))
        else:
            radius_str = f"{self.radius:.1f}"

        # 创建标签
        radius_label = MathTex(
            rf"r={radius_str}",
            font_size=20,
            color=color
        )

        # 放置在半径线中点上方（相对于局部圆心）
        mid_point = self._center_point_local + self.radius_line_end / 2
        radius_label.move_to(mid_point).shift(UP * 0.3 + RIGHT * 0.2)

        return radius_label

        return label
