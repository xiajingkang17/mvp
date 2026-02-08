"""
物理力学组件库

包含19种常用的物理力学组件
所有组件都是纯静态可视化，继承自 VGroup

作者: Manim 物理组件库
日期: 2026-02-08
"""

from __future__ import annotations

import math
import numpy as np
from manim import *
from typing import Optional, List, Tuple


# ============================================
# 0. 完整演示组件（保留旧版）
# ============================================

class InclinedPlaneGroup(VGroup):
    """
    斜面滑块受力分析组件

    这是一个完整的物理演示组件，展示滑块在斜面上的受力分析。

    参数:
        angle (float): 斜面角度（度数），默认 30 度
        length (float): 斜面底边长度，默认 5.0
        block_width (float): 滑块宽度，默认 1.0
        block_height (float): 滑块高度，默认 0.6
        show_forces (bool): 是否显示受力分析，默认 True
        show_angle (bool): 是否显示角度标注，默认 True

    示例:
        >>> plane = InclinedPlaneGroup(angle=30, length=5)
        >>> self.add(plane)
    """

    def __init__(
        self,
        angle: float = 30,
        length: float = 5.0,
        block_width: float = 1.0,
        block_height: float = 0.6,
        show_forces: bool = True,
        show_angle: bool = True,
        **kwargs
    ):
        super().__init__(**kwargs)

        # 将角度转换为弧度
        angle_rad = angle * DEGREES

        # 1. 创建斜面（直角三角形）
        # ============================================
        # 计算三角形顶点
        # 顶点顺序：底边右端 -> 底边左端 -> 斜边顶端
        triangle_height = length * math.tan(angle_rad)

        inclined_plane = Polygon(
            [length/2, 0, 0],           # 底边右端点
            [-length/2, 0, 0],          # 底边左端点
            [-length/2, triangle_height, 0],  # 斜边顶点
            color=BLUE_B,
            fill_opacity=0.3,
            stroke_width=3
        )
        self.inclined_plane = inclined_plane

        # 2. 创建滑块（矩形）
        # ============================================
        block = Rectangle(
            width=block_width,
            height=block_height,
            color=ORANGE,
            fill_opacity=0.8,
            stroke_width=2
        )

        # 计算滑块在斜面上的位置
        # 滑块中心应该位于斜面的中点附近
        slope_center_x = 0  # 斜面水平中心
        slope_center_y = triangle_height / 2  # 斜面垂直中心

        # 旋转滑块，使其贴合斜面
        block.rotate(angle_rad, about_point=ORIGIN)

        # 将滑块移动到斜面上
        # 需要根据斜面角度计算滑块的位置
        block_position = self._calculate_block_position(
            angle, length, triangle_height, block_width, block_height
        )
        block.move_to(block_position)

        self.block = block

        # 3. 创建角度标注
        # ============================================
        if show_angle:
            angle_arc = self._create_angle_arc(angle, length)
            angle_label = MathTex(r"\theta", font_size=36).next_to(
                angle_arc,
                direction=DOWN + RIGHT,
                buff=0.1
            )
            self.angle_arc = angle_arc
            self.angle_label = angle_label
        else:
            self.angle_arc = None
            self.angle_label = None

        # 4. 创建受力分析箭头
        # ============================================
        if show_forces:
            # 获取滑块中心点（箭头起点）
            block_center = block.get_center()

            # 重力 (mg) - 竖直向下，红色
            gravity_vector = self._create_force_vector(
                start_point=block_center,
                direction=DOWN,
                length=1.5,
                color=RED,
                label=r"mg"
            )
            self.gravity = gravity_vector

            # 支持力 (F_N) - 垂直于斜面向上，蓝色
            # 计算垂直于斜面的方向：角度 + 90度
            normal_direction = rotate_vector(UP, angle_rad)
            normal_vector = self._create_force_vector(
                start_point=block_center,
                direction=normal_direction,
                length=1.5,
                color=BLUE,
                label=r"F_N"
            )
            self.normal_force = normal_vector

            # 摩擦力 (f) - 沿斜面向上，绿色
            # 计算沿斜面向上的方向：角度 - 90度（相对于水平线）
            friction_direction = rotate_vector(LEFT, angle_rad)
            friction_vector = self._create_force_vector(
                start_point=block_center,
                direction=friction_direction,
                length=1.2,
                color=GREEN,
                label=r"f"
            )
            self.friction = friction_vector
        else:
            self.gravity = None
            self.normal_force = None
            self.friction = None

        # 5. 将所有元素添加到 VGroup
        # ============================================
        self.add(inclined_plane)
        self.add(block)

        if show_angle:
            self.add(angle_arc)
            self.add(angle_label)

        if show_forces:
            self.add(gravity_vector)
            self.add(normal_vector)
            self.add(friction_vector)

    def _calculate_block_position(
        self,
        angle: float,
        length: float,
        triangle_height: float,
        block_width: float,
        block_height: float
    ) -> np.ndarray:
        """
        计算滑块在斜面上的位置

        Args:
            angle: 斜面角度（度）
            length: 底边长度
            triangle_height: 三角形高度
            block_width: 滑块宽度
            block_height: 滑块高度

        Returns:
            滑块中心坐标 [x, y, 0]
        """
        angle_rad = angle * DEGREES

        # 滑块沿斜面方向距离底部的距离（斜面中点位置）
        distance_along_slope = math.sqrt(length**2 + triangle_height**2) / 2

        # 计算滑块底面中心在斜面上的位置
        # 斜面起点在左下角 (-length/2, 0)
        start_x = -length/2
        start_y = 0

        # 沿斜面方向移动
        slope_x = start_x + distance_along_slope * math.cos(angle_rad)
        slope_y = start_y + distance_along_slope * math.sin(angle_rad)

        # 滑块中心需要从底面向上偏移 block_height/2（垂直于斜面方向）
        # 垂直于斜面的方向向量
        normal_x = -math.sin(angle_rad)
        normal_y = math.cos(angle_rad)

        center_x = slope_x + (block_height / 2) * normal_x
        center_y = slope_y + (block_height / 2) * normal_y

        return np.array([center_x, center_y, 0])

    def _create_angle_arc(
        self,
        angle: float,
        length: float
    ) -> Arc:
        """
        创建角度标注弧线

        Args:
            angle: 角度值（度）
            length: 底边长度

        Returns:
            弧线对象
        """
        # 创建弧线，从 0 度到 angle 度
        arc = Arc(
            radius=0.8,
            start_angle=0,
            angle=angle * DEGREES,
            color=WHITE,
            stroke_width=2
        )

        # 将弧线移动到斜面底角位置
        arc.shift([-length/2, 0, 0])

        return arc

    def _create_force_vector(
        self,
        start_point: np.ndarray,
        direction: np.ndarray,
        length: float = 1.5,
        color: str = YELLOW,
        label: str = ""
    ) -> VGroup:
        """
        创建力向量箭头及其标签

        Args:
            start_point: 箭头起点坐标
            direction: 方向向量
            length: 箭头长度
            color: 颜色
            label: LaTeX 标签

        Returns:
            包含箭头和标签的 VGroup
        """
        # 归一化方向向量
        direction = direction / np.linalg.norm(direction)

        # 计算箭头终点
        end_point = start_point + direction * length

        # 创建箭头
        arrow = Arrow(
            start_point,
            end_point,
            buff=0,
            color=color,
            stroke_width=4,
            max_tip_length_to_length_ratio=0.3
        )

        result = VGroup(arrow)

        # 如果有标签，创建标签并放在箭头末端
        if label:
            label_tex = MathTex(label, font_size=32, color=color)
            # 将标签放在箭头末端附近
            label_position = end_point + direction * 0.3
            label_tex.move_to(label_position)

            result.add(label_tex)

        return result

    def slide_block(self, distance: float = 0.5) -> Animation:
        """
        创建滑块沿斜面滑动的动画

        Args:
            distance: 滑动距离

        Returns:
            Manim 动画对象
        """
        angle_rad = self.get_angle() * DEGREES
        direction = np.array([math.cos(angle_rad), math.sin(angle_rad), 0])

        return self.block.animate.shift(direction * distance)

    def get_angle(self) -> float:
        """获取斜面角度"""
        # 从斜面三角形的顶点计算角度
        # 这里简化处理，返回构造时的角度值
        # 在实际应用中可以从几何形状反推
        return 30  # 默认值，可根据需要改进

    def show_force_analysis(self) -> Animation:
        """
        创建依次显示各个力的动画

        Returns:
            Succession 动画序列
        """
        animations = []

        if self.gravity:
            animations.append(Create(self.gravity))
        if self.normal_force:
            animations.append(Create(self.normal_force))
        if self.friction:
            animations.append(Create(self.friction))

        if animations:
            return Succession(*animations)
        else:
            return Wait(0)


# ============================================
# 1. 基础环境组件
# ============================================

class Wall(VGroup):
    """
    墙面/地面组件

    画一条主直线，在下方画出等间距短斜线表示固定面
    阴影线方向：向右下方倾斜（-45度）
    """

    def __init__(
        self,
        length: float = 8.0,
        angle: float = 0,  # 0=水平地面, 90=垂直墙面
        hatch_spacing: float = 0.4,
        hatch_length: float = 0.25,
        color: str = WHITE,
        stroke_width: float = 4.0,
        **kwargs
    ):
        super().__init__(**kwargs)

        # 主直线（水平）
        main_line = Line(
            start=[-length/2, 0, 0],
            end=[length/2, 0, 0],
            color=color,
            stroke_width=stroke_width
        )

        # 创建等间距的短斜线（阴影）
        # 阴影线方向：向右下方倾斜（-45度）
        hatch_lines = VGroup()
        num_hatches = int(length / hatch_spacing)

        # -45度角的方向向量
        hatch_angle = -45 * DEGREES
        hatch_direction = np.array([
            math.cos(hatch_angle),
            math.sin(hatch_angle),
            0
        ])

        for i in range(num_hatches):
            x = -length/2 + i * hatch_spacing

            # 阴影线起点（在主直线上）
            start_point = np.array([x, 0, 0])

            # 阴影线终点（向右下方）
            end_point = start_point + hatch_direction * hatch_length

            hatch = Line(
                start=start_point,
                end=end_point,
                color=color,
                stroke_width=stroke_width * 0.6  # 阴影线稍细
            )
            hatch_lines.add(hatch)

        self.add(main_line, hatch_lines)


class InclinedPlane(VGroup):
    """
    斜面组件

    直角三角形，左下角为直角，右下角标注角度 θ
    """

    def __init__(
        self,
        angle: float = 30,
        length: float = 5.0,
        color: str = WHITE,
        stroke_width: float = 4.0,
        fill_color: str = BLUE_E,
        fill_opacity: float = 0.3,
        show_angle: bool = True,
        **kwargs
    ):
        super().__init__(**kwargs)

        angle_rad = angle * DEGREES
        height = length * math.tan(angle_rad)

        # 定义三个顶点
        # 左下角：直角 (90°)
        p_bottom_left = ORIGIN
        # 右下角：斜面底角（要标注 θ）
        p_bottom_right = RIGHT * length
        # 左上角：顶点
        p_top_left = UP * height

        # 绘制直角三角形
        triangle = Polygon(
            p_bottom_left,
            p_bottom_right,
            p_top_left,
            color=color,
            stroke_width=stroke_width,
            fill_color=fill_color,
            fill_opacity=fill_opacity
        )

        self.add(triangle)

        # 角度标注（在右下角）
        if show_angle:
            # 角度弧线
            # 从底边开始（角度0），逆时针旋转到斜边
            arc_radius = 0.6
            angle_arc = Arc(
                radius=arc_radius,
                start_angle=PI,  # 从左边开始（180度）
                angle=-angle_rad,  # 顺时针旋转 -angle 度
                color=color,
                stroke_width=stroke_width * 0.8
            )
            # 将弧线移到右下角
            angle_arc.shift(p_bottom_right)

            # 角度标签 θ
            angle_label = MathTex(r"\theta", font_size=36, color=color)
            # 将标签放在弧线的左侧
            label_offset = np.array([
                -arc_radius * 1.2,
                arc_radius * 0.3,
                0
            ])
            angle_label.move_to(p_bottom_right + label_offset)

            self.add(angle_arc, angle_label)


# ============================================
# 2. 刚体与物体组件
# ============================================

class Block(VGroup):
    """
    滑块组件

    简单的矩形，白边黑底
    """

    def __init__(
        self,
        width: float = 1.5,
        height: float = 1.0,
        label: str = "m",
        label_color: str = WHITE,
        color: str = WHITE,
        stroke_width: float = 4.0,
        **kwargs
    ):
        super().__init__(**kwargs)

        # 矩形主体
        body = Rectangle(
            width=width,
            height=height,
            stroke_color=color,
            stroke_width=stroke_width,
            fill_color=BLACK,
            fill_opacity=1.0
        )

        self.add(body)

        # 文字标签
        if label:
            label_text = Tex(label, font_size=36, color=label_color)
            label_text.move_to(body.get_center())
            self.add(label_text)


class Cart(VGroup):
    """
    小车组件

    上方扁长方形（车身），下方两个圆形（车轮）
    """

    def __init__(
        self,
        width: float = 2.5,
        height: float = 0.8,
        wheel_radius: float = 0.3,
        color: str = WHITE,
        stroke_width: float = 4.0,
        **kwargs
    ):
        super().__init__(**kwargs)

        # 车身
        body = Rectangle(
            width=width,
            height=height,
            stroke_color=color,
            stroke_width=stroke_width,
            fill_color=BLACK,
            fill_opacity=1.0
        )

        # 左车轮
        left_wheel = Circle(
            radius=wheel_radius,
            color=color,
            stroke_width=stroke_width,
            fill_color=BLACK,
            fill_opacity=1.0
        ).shift([
            -width/4,
            -height/2 - wheel_radius,
            0
        ])

        # 右车轮
        right_wheel = Circle(
            radius=wheel_radius,
            color=color,
            stroke_width=stroke_width,
            fill_color=BLACK,
            fill_opacity=1.0
        ).shift([
            width/4,
            -height/2 - wheel_radius,
            0
        ])

        # 车轮轴心点
        left_axle = Dot(
            point=left_wheel.get_center(),
            radius=0.05,
            color=color
        )

        right_axle = Dot(
            point=right_wheel.get_center(),
            radius=0.05,
            color=color
        )

        self.add(body, left_wheel, right_wheel, left_axle, right_axle)


class Weight(VGroup):
    """
    钩码/砝码组件

    教科书标准样式：上方圆环挂钩 + 下方矩形主体
    """

    def __init__(
        self,
        width: float = 1.0,
        height: float = 1.5,
        hook_radius: float = 0.15,
        color: str = WHITE,
        stroke_width: float = 4.0,
        **kwargs
    ):
        super().__init__(**kwargs)

        # 矩形主体（白边黑底）
        body = Rectangle(
            width=width,
            height=height,
            stroke_color=color,
            stroke_width=stroke_width,
            fill_color=BLACK,
            fill_opacity=1.0
        )

        # 上方圆环挂钩
        # 位置：矩形顶部中央
        hook_y = height/2 + hook_radius
        hook_ring = Annulus(
            inner_radius=hook_radius * 0.6,
            outer_radius=hook_radius,
            color=color,
            stroke_width=stroke_width,
            fill_opacity=0
        ).shift([0, hook_y, 0])

        self.add(hook_ring, body)


# ============================================
# 3. 连接装置组件
# ============================================

class Pulley(VGroup):
    """
    滑轮组件（基类）- 中心轴样式

    圆形轮子 + 中心轴 + 固定杆
    """

    def __init__(
        self,
        radius: float = 0.5,
        rod_angle: float = 90 * DEGREES,  # 固定杆角度，默认向上
        color: str = WHITE,
        stroke_width: float = 4.0,
        **kwargs
    ):
        super().__init__(**kwargs)

        # 1. 轮子（白边黑底）
        wheel = Circle(
            radius=radius,
            color=color,
            stroke_width=stroke_width,
            fill_color=BLACK,
            fill_opacity=1.0
        )

        # 2. 中心轴点（小白点）
        axle = Dot(
            point=ORIGIN,
            radius=0.05,
            color=color
        )

        # 3. 固定杆（从中心伸出）
        rod_length = radius * 1.5
        rod = Line(
            start=ORIGIN,
            end=RIGHT * rod_length,
            color=color,
            stroke_width=stroke_width
        )

        # 4. 根据传入的角度旋转杆子
        rod.rotate(rod_angle, about_point=ORIGIN)

        # 5. 组合（杆子最底层 -> 轮子 -> 轴心最上层）
        self.add(rod, wheel, axle)

        # 保存引用以便后续访问
        self.wheel = wheel
        self.axle = axle
        self.rod = rod


class FixedPulley(Pulley):
    """
    定滑轮

    继承自 Pulley，支架上方延伸出固定杆
    """

    def __init__(
        self,
        radius: float = 0.5,
        rod_length: float = 1.0,
        color: str = WHITE,
        stroke_width: float = 4.0,
        **kwargs
    ):
        # 调用父类初始化（但不添加到场景）
        super(VGroup, self).__init__(**kwargs)

        # 创建基础滑轮
        base_pulley = Pulley(
            radius=radius,
            color=color,
            stroke_width=stroke_width
        )

        # 上方固定杆
        fixed_rod = Line(
            start=[0, radius * 1.5, 0],
            end=[0, radius * 1.5 + rod_length, 0],
            color=color,
            stroke_width=stroke_width
        )

        self.add(base_pulley, fixed_rod)


class MovablePulley(Pulley):
    """
    动滑轮

    继承自 Pulley，支架下方延伸出挂钩
    """

    def __init__(
        self,
        radius: float = 0.5,
        hook_length: float = 0.6,
        color: str = WHITE,
        stroke_width: float = 4.0,
        **kwargs
    ):
        # 调用父类初始化（但不添加到场景）
        super(VGroup, self).__init__(**kwargs)

        # 创建基础滑轮
        base_pulley = Pulley(
            radius=radius,
            color=color,
            stroke_width=stroke_width
        )

        # 下方挂钩（J形）
        hook_start = np.array([0, -radius * 0.8, 0])
        hook_end = np.array([0, -radius * 0.8 - hook_length, 0])

        # 挂钩直线部分
        hook_line = Line(
            start=hook_start,
            end=hook_end,
            color=color,
            stroke_width=stroke_width
        )

        # 挂钩底部弯曲
        hook_curve = Arc(
            radius=hook_length * 0.2,
            start_angle=PI/2,
            angle=PI,
            color=color,
            stroke_width=stroke_width
        )
        hook_curve.move_to(hook_end)

        self.add(base_pulley, hook_line, hook_curve)


class Rope(VGroup):
    """
    绳组件

    简单的直线
    """

    def __init__(
        self,
        length: float = 4.0,
        angle: float = 0,
        color: str = GRAY,
        stroke_width: float = 3.0,
        **kwargs
    ):
        super().__init__(**kwargs)

        angle_rad = angle * DEGREES
        start_point = np.array([
            -length/2 * math.cos(angle_rad),
            -length/2 * math.sin(angle_rad),
            0
        ])
        end_point = np.array([
            length/2 * math.cos(angle_rad),
            length/2 * math.sin(angle_rad),
            0
        ])

        rope = Line(
            start=start_point,
            end=end_point,
            color=color,
            stroke_width=stroke_width
        )

        self.add(rope)


class Spring(VGroup):
    """
    弹簧组件

    锯齿状线条
    """

    def __init__(
        self,
        length: float = 4.0,
        height: float = 0.6,
        num_coils: int = 8,
        end_length: float = 0.5,
        color: str = WHITE,
        stroke_width: float = 3.0,
        **kwargs
    ):
        super().__init__(**kwargs)

        # 计算弹簧参数
        coil_width = (length - 2 * end_length) / num_coils

        # 左端直线
        left_end = Line(
            start=[-length/2, 0, 0],
            end=[-length/2 + end_length, 0, 0],
            color=color,
            stroke_width=stroke_width
        )

        # 锯齿部分
        zigzag_points = [[-length/2 + end_length, 0, 0]]

        for i in range(num_coils):
            x_start = -length/2 + end_length + i * coil_width
            # 上点
            zigzag_points.append([x_start + coil_width/2, height/2, 0])
            # 下点
            zigzag_points.append([x_start + coil_width, -height/2, 0])

        zigzag_points.append([length/2 - end_length, 0, 0])

        zigzag = VMobject()
        zigzag.set_points_as_corners(zigzag_points)
        zigzag.set_color(color)
        zigzag.set_stroke(width=stroke_width)

        # 右端直线
        right_end = Line(
            start=[length/2 - end_length, 0, 0],
            end=[length/2, 0, 0],
            color=color,
            stroke_width=stroke_width
        )

        self.add(left_end, zigzag, right_end)


class Rod(VGroup):
    """
    杆组件

    细长矩形表示刚性杆（教科书标准样式）
    """

    def __init__(
        self,
        length: float = 4.0,
        thickness: float = 0.15,
        color: str = WHITE,
        stroke_width: float = 4.0,
        **kwargs
    ):
        super().__init__(**kwargs)

        # 细长矩形（白边黑底）
        rod = Rectangle(
            width=length,
            height=thickness,
            stroke_color=color,
            stroke_width=stroke_width,
            fill_color=BLACK,
            fill_opacity=1.0
        )

        self.add(rod)


class Hinge(VGroup):
    """
    铰链/销钉关节组件

    简单的圆环+中心点样式，用于连接杆件
    """

    def __init__(
        self,
        radius: float = 0.2,
        color: str = WHITE,
        stroke_width: float = 4.0,
        **kwargs
    ):
        super().__init__(**kwargs)

        # 外圆环（白边黑底，遮挡下层杆件）
        outer_ring = Circle(
            radius=radius,
            color=color,
            stroke_width=stroke_width,
            fill_color=BLACK,
            fill_opacity=1.0
        )

        # 中心小白点（表示转轴）
        center_dot = Dot(
            point=ORIGIN,
            radius=0.04,
            color=color
        )

        self.add(outer_ring, center_dot)


# ============================================
# 4. 复杂轨道与槽车组件
# ============================================

class CircularGroove(VGroup):
    """
    圆槽组件

    两条同心圆弧形成的凹槽
    """

    def __init__(
        self,
        radius: float = 2.0,
        groove_width: float = 0.3,
        color: str = WHITE,
        stroke_width: float = 4.0,
        **kwargs
    ):
        super().__init__(**kwargs)

        # 外圆
        outer_circle = Circle(
            radius=radius + groove_width/2,
            color=color,
            stroke_width=stroke_width,
            fill_opacity=0
        )

        # 内圆
        inner_circle = Circle(
            radius=radius - groove_width/2,
            color=color,
            stroke_width=stroke_width,
            fill_opacity=0
        )

        # 填充（表示槽）
        fill_region = Annulus(
            inner_radius=radius - groove_width/2,
            outer_radius=radius + groove_width/2,
            color=color,
            stroke_width=0,
            fill_opacity=0.2
        )

        self.add(outer_circle, inner_circle, fill_region)


class SemicircleGroove(VGroup):
    """
    半圆槽组件

    180度的圆弧槽（碗状）
    """

    def __init__(
        self,
        radius: float = 2.0,
        groove_width: float = 0.3,
        color: str = WHITE,
        stroke_width: float = 4.0,
        **kwargs
    ):
        super().__init__(**kwargs)

        # 外圆弧
        outer_arc = Arc(
            radius=radius + groove_width/2,
            start_angle=0,
            angle=PI,
            color=color,
            stroke_width=stroke_width
        )

        # 内圆弧
        inner_arc = Arc(
            radius=radius - groove_width/2,
            start_angle=0,
            angle=PI,
            color=color,
            stroke_width=stroke_width
        )

        # 填充
        fill_shape = Arc(
            radius=radius,
            start_angle=0,
            angle=PI,
            color=color,
            stroke_width=groove_width,
            stroke_opacity=0.2
        )

        self.add(outer_arc, inner_arc, fill_shape)


class QuarterCircleGroove(VGroup):
    """
    1/4圆槽组件

    90度的圆弧槽
    """

    def __init__(
        self,
        radius: float = 2.0,
        groove_width: float = 0.3,
        corner: str = "bottom_left",  # bottom_left, bottom_right, top_left, top_right
        color: str = WHITE,
        stroke_width: float = 4.0,
        **kwargs
    ):
        super().__init__(**kwargs)

        # 根据角落位置确定起始角度
        start_angles = {
            "bottom_left": 0,
            "bottom_right": PI/2,
            "top_right": PI,
            "top_left": 3*PI/2
        }
        start_angle = start_angles.get(corner, 0)

        # 外圆弧
        outer_arc = Arc(
            radius=radius + groove_width/2,
            start_angle=start_angle,
            angle=PI/2,
            color=color,
            stroke_width=stroke_width
        )

        # 内圆弧
        inner_arc = Arc(
            radius=radius - groove_width/2,
            start_angle=start_angle,
            angle=PI/2,
            color=color,
            stroke_width=stroke_width
        )

        # 填充
        fill_shape = Arc(
            radius=radius,
            start_angle=start_angle,
            angle=PI/2,
            color=color,
            stroke_width=groove_width,
            stroke_opacity=0.2
        )

        self.add(outer_arc, inner_arc, fill_shape)


class SemicircleCart(VGroup):
    """
    半圆槽车组件

    使用"饼干切割"方法：用完整的圆切割矩形，产生完美的半圆槽
    """

    def __init__(
        self,
        height: float = 2.0,
        wheel_radius: float = 0.25,
        color: str = WHITE,
        stroke_width: float = 4.0,
        **kwargs
    ):
        super().__init__(**kwargs)

        # 1. 定义尺寸（2:1 长宽比）
        body_height = height
        body_width = body_height * 2.0
        groove_radius = body_height * 0.9  # 切割圆的半径略小于矩形高度

        # 2. 创建基础矩形
        base_rect = Rectangle(
            width=body_width,
            height=body_height,
            color=color,
            stroke_width=stroke_width,
            fill_color=BLACK,
            fill_opacity=1.0
        )

        # 3. 创建完整的圆作为切割工具（关键：使用完整圆，不是半圆）
        cutter_circle = Circle(
            radius=groove_radius,
            color=color,
            stroke_width=stroke_width,
            fill_color=BLACK,
            fill_opacity=1.0
        )

        # 将圆的圆心对齐到矩形的顶部边中点
        # 这样圆的下半部分会切掉矩形的上半部分，形成完美的半圆槽
        cutter_circle.move_to(base_rect.get_top())

        # 4. 执行布尔减法：矩形 - 圆 = 带半圆槽的车体
        cart_body = Difference(base_rect, cutter_circle)
        cart_body.set_style(
            stroke_color=color,
            stroke_width=stroke_width,
            fill_color=BLACK,
            fill_opacity=1.0
        )

        # 5. 创建轮子
        left_wheel = Circle(
            radius=wheel_radius,
            color=color,
            stroke_width=stroke_width,
            fill_color=BLACK,
            fill_opacity=1.0
        )

        right_wheel = Circle(
            radius=wheel_radius,
            color=color,
            stroke_width=stroke_width,
            fill_color=BLACK,
            fill_opacity=1.0
        )

        # 轮子位于车体底部下方
        wheel_y = cart_body.get_bottom()[1] - wheel_radius
        wheel_x_offset = body_width * 0.25  # 距离中心 1/4 宽度

        left_wheel.move_to(ORIGIN).shift(LEFT * wheel_x_offset + UP * wheel_y)
        right_wheel.move_to(ORIGIN).shift(RIGHT * wheel_x_offset + UP * wheel_y)

        # 6. 组合并居中
        self.add(cart_body, left_wheel, right_wheel)
        self.move_to(ORIGIN)


class QuarterCart(VGroup):
    """
    1/4圆槽车组件

    使用布尔减法：正方形 - 圆（圆心在右上角）= 带四分之一圆槽的车体
    """

    def __init__(
        self,
        side_length: float = 2.0,
        wheel_radius: float = 0.25,
        color: str = WHITE,
        stroke_width: float = 4.0,
        **kwargs
    ):
        super().__init__(**kwargs)

        # 1. 创建基础正方形
        base_square = Square(
            side_length=side_length,
            color=color,
            stroke_width=stroke_width,
            fill_color=BLACK,
            fill_opacity=1.0
        )

        # 2. 创建完整的圆作为切割工具
        # 半径略小于正方形边长
        groove_radius = side_length * 0.9
        cutter_circle = Circle(
            radius=groove_radius,
            color=color,
            stroke_width=stroke_width,
            fill_color=BLACK,
            fill_opacity=1.0
        )

        # 3. 将圆的圆心对齐到正方形的右上角
        # 这样圆的左下四分之一会切入正方形，形成四分之一圆槽
        cutter_circle.move_to(base_square.get_corner(UR))

        # 4. 执行布尔减法：正方形 - 圆
        cart_body = Difference(base_square, cutter_circle)
        cart_body.set_style(
            stroke_color=color,
            stroke_width=stroke_width,
            fill_color=BLACK,
            fill_opacity=1.0
        )

        # 5. 创建轮子
        left_wheel = Circle(
            radius=wheel_radius,
            color=color,
            stroke_width=stroke_width,
            fill_color=BLACK,
            fill_opacity=1.0
        )

        right_wheel = Circle(
            radius=wheel_radius,
            color=color,
            stroke_width=stroke_width,
            fill_color=BLACK,
            fill_opacity=1.0
        )

        # 轮子位于车体底部下方
        wheel_y = cart_body.get_bottom()[1] - wheel_radius
        wheel_x_offset = side_length * 0.25  # 距离中心 1/4 边长

        left_wheel.move_to(ORIGIN).shift(LEFT * wheel_x_offset + UP * wheel_y)
        right_wheel.move_to(ORIGIN).shift(RIGHT * wheel_x_offset + UP * wheel_y)

        # 6. 组合并居中
        self.add(cart_body, left_wheel, right_wheel)
        self.move_to(ORIGIN)


# ============================================
# 5. 测量工具组件
# ============================================

class SpringScale(VGroup):
    """
    弹簧测力器组件

    标准示意图：外壳 + 顶部圆环 + 刻度线 + 指针 + 底部挂钩
    """

    def __init__(
        self,
        width: float = 1.0,
        height: float = 3.5,
        reading: float = 0.5,  # 0.0 到 1.0，控制指针位置
        color: str = WHITE,
        stroke_width: float = 4.0,
        **kwargs
    ):
        super().__init__(**kwargs)

        # 1. 主体外壳（居中）
        body = Rectangle(
            width=width,
            height=height,
            color=color,
            stroke_width=stroke_width
        )
        body.set_fill(BLACK, opacity=1)  # 黑色填充，遮挡背景
        body.move_to(ORIGIN)

        # 2. 内部刻度范围（关键修正）
        # 在矩形内部留出边距
        padding = height * 0.15
        top_y = body.get_top()[1] - padding
        bottom_y = body.get_bottom()[1] + padding

        # 3. 中间竖线
        center_line = Line(
            start=[0, top_y, 0],
            end=[0, bottom_y, 0],
            color=color,
            stroke_width=stroke_width * 0.5
        )

        # 4. 生成刻度（在 top_y 和 bottom_y 之间）
        scale_marks = VGroup()
        num_major_ticks = 5
        num_minor_ticks = 20

        for i in range(num_minor_ticks + 1):
            # 线性插值计算 y（从上到下）
            alpha = i / num_minor_ticks
            y = top_y * (1 - alpha) + bottom_y * alpha

            # 判断是否为主刻度
            is_major = (i % (num_minor_ticks // num_major_ticks) == 0)
            mark_length = width * 0.35 if is_major else width * 0.2
            mark_width = stroke_width * 0.8 if is_major else stroke_width * 0.5

            # 左侧刻度线
            tick_start_x = -width/2 + 0.1
            tick = Line(
                start=[tick_start_x, y, 0],
                end=[tick_start_x + mark_length, y, 0],
                color=color,
                stroke_width=mark_width
            )
            scale_marks.add(tick)

            # 如果是主刻度，添加数字标签
            if is_major:
                tick_num = i // (num_minor_ticks // num_major_ticks)
                label = Text(
                    str(tick_num),
                    font_size=16,
                    color=color
                )
                label.move_to([tick_start_x + mark_length + 0.15, y, 0])
                scale_marks.add(label)

        # 5. 指针（根据 reading 参数调整位置）
        alpha = reading
        pointer_y = top_y * (1 - alpha) + bottom_y * alpha

        # 指针主体（水平线）
        pointer = Line(
            start=[-width * 0.25, pointer_y, 0],
            end=[width * 0.25, pointer_y, 0],
            color=YELLOW,
            stroke_width=stroke_width * 0.8
        )

        # 指针箭头（右侧）
        arrowhead = Polygon(
            [width * 0.25, pointer_y, 0],
            [width * 0.15, pointer_y - 0.08, 0],
            [width * 0.15, pointer_y + 0.08, 0],
            color=YELLOW,
            stroke_width=stroke_width * 0.6
        )
        arrowhead.set_fill(YELLOW, opacity=1)

        # 6. 顶部圆环
        ring_radius = width * 0.25
        top_ring = Annulus(
            inner_radius=ring_radius * 0.6,
            outer_radius=ring_radius,
            color=color,
            stroke_width=stroke_width
        )
        top_ring.next_to(body, UP, buff=0)
        top_ring.set_x(0)  # 强制水平居中

        # 7. 底部挂钩（J形）
        hook_radius = width * 0.15
        hook = Arc(
            radius=hook_radius,
            start_angle=PI,
            angle=PI,
            color=color,
            stroke_width=stroke_width
        )
        # 旋转让钩子开口向左
        hook.rotate(-PI/2)
        # 移动到矩形底部
        hook.next_to(body, DOWN, buff=0)
        # 强制水平居中（修正歪的问题）
        hook.set_x(0)

        # 8. 组合（注意顺序：先 add body，再 add 其他部件）
        self.add(body, center_line, scale_marks, pointer, arrowhead, top_ring, hook)
