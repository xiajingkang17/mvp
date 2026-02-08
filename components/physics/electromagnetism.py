"""
电磁学组件库 - Electromagnetism Components

包含专业的电磁学元件：电源、电感线圈等
所有组件都遵循教科书风格，继承自 VGroup
"""

from __future__ import annotations

import numpy as np
from manim import *
from typing import Optional, Union


class Battery(VGroup):
    """
    直流电源组件（中国高中教材标准样式）

    符号结构：
    - 正极：细长竖线
    - 负极：粗短竖线
    - 背景：黑色遮罩，确保遮挡网格线

    参数:
        height: 正极板高度，默认 0.8
        ratio: 负极高度与正极高度的比例，默认 0.55
        plate_spacing: 两极板间距，默认 0.3
        wire_length: 引线长度，默认 0.5
        is_positive_left: 正极是否在左侧，默认 True
        color: 线条颜色，默认 WHITE
        stroke_width: 线条宽度，默认 4.0
    """

    def __init__(
        self,
        height: float = 0.8,
        ratio: float = 0.55,
        plate_spacing: float = 0.3,
        wire_length: float = 0.5,
        is_positive_left: bool = True,
        color: str = WHITE,
        stroke_width: float = 4.0,
        **kwargs
    ):
        super().__init__(**kwargs)

        # 计算极板高度
        positive_height = height
        negative_height = height * ratio

        # 计算组件总宽度（用于背景遮罩）
        total_width = 2 * wire_length + plate_spacing

        # Step 1: 创建背景遮罩（关键：遮挡网格线）
        # 使用透明矩形 + 白色边框的方法
        # 高度略大于正极，确保完全覆盖
        mask_height = positive_height * 1.5
        background_mask = Rectangle(
            width=total_width,
            height=mask_height,
            stroke_color=BLACK,       # 黑色边框（与背景同色）
            stroke_width=0,           # 无边框
            fill_color=BLACK,         # 黑色填充
            fill_opacity=1.0          # 完全不透明
        )
        background_mask.move_to(ORIGIN)
        # 关键：将遮罩放在最底层
        background_mask.z_index = -10

        # Step 2: 创建正极板（长线）
        positive_plate = Line(
            start=[0, -positive_height/2, 0],
            end=[0, positive_height/2, 0],
            color=color,
            stroke_width=stroke_width
        )

        # Step 3: 创建负极板（短线）
        # 注意：负极可以用稍粗的线宽来表示"粗短"的视觉效果
        negative_plate = Line(
            start=[0, -negative_height/2, 0],
            end=[0, negative_height/2, 0],
            color=color,
            stroke_width=stroke_width * 1.2  # 稍粗以示区别
        )

        # Step 4: 创建引线
        # 左侧引线
        left_wire = Line(
            start=[-wire_length, 0, 0],
            end=[0, 0, 0],
            color=color,
            stroke_width=stroke_width
        )

        # 右侧引线
        right_wire = Line(
            start=[0, 0, 0],
            end=[wire_length, 0, 0],
            color=color,
            stroke_width=stroke_width
        )

        # Step 5: 根据参数调整极板位置
        if is_positive_left:
            # 左正右负
            positive_plate.shift(LEFT * plate_spacing / 2)
            negative_plate.shift(RIGHT * plate_spacing / 2)

            # 左引线连接到正极
            left_wire_end = positive_plate.get_center()[0]
            left_wire.put_start_and_end_on(
                [-wire_length, 0, 0],
                [left_wire_end, 0, 0]
            )

            # 右引线连接到负极
            right_wire_start = negative_plate.get_center()[0]
            right_wire.put_start_and_end_on(
                [right_wire_start, 0, 0],
                [right_wire_start + wire_length, 0, 0]
            )
        else:
            # 左负右正
            negative_plate.shift(LEFT * plate_spacing / 2)
            positive_plate.shift(RIGHT * plate_spacing / 2)

            # 左引线连接到负极
            left_wire_end = negative_plate.get_center()[0]
            left_wire.put_start_and_end_on(
                [-wire_length, 0, 0],
                [left_wire_end, 0, 0]
            )

            # 右引线连接到正极
            right_wire_start = positive_plate.get_center()[0]
            right_wire.put_start_and_end_on(
                [right_wire_start, 0, 0],
                [right_wire_start + wire_length, 0, 0]
            )

        # Step 6: 组合（关键顺序：Mask -> Wires -> Plates）
        # 在 VGroup 中，z_index 控制渲染层级，数值越小越在底层

        # 设置所有元素的 z_index
        background_mask.z_index = -10   # 最底层（遮罩）
        left_wire.z_index = 0           # 中间层（引线）
        right_wire.z_index = 0
        positive_plate.z_index = 10     # 最顶层（极板）
        negative_plate.z_index = 10

        # 按顺序添加到 VGroup
        self.add(background_mask)
        self.add(left_wire, right_wire)
        self.add(positive_plate, negative_plate)

        # 保存引用以便访问
        self.background_mask = background_mask
        self.positive_plate = positive_plate
        self.negative_plate = negative_plate
        self.left_wire = left_wire
        self.right_wire = right_wire
        self.is_positive_left = is_positive_left

    def get_positive_terminal(self) -> np.ndarray:
        """
        获取正极接线端点坐标

        Returns:
            正极端点的三维坐标 [x, y, z]
        """
        if self.is_positive_left:
            return self.left_wire.get_start()
        else:
            return self.right_wire.get_end()

    def get_negative_terminal(self) -> np.ndarray:
        """
        获取负极接线端点坐标

        Returns:
            负极端点的三维坐标 [x, y, z]
        """
        if self.is_positive_left:
            return self.right_wire.get_end()
        else:
            return self.left_wire.get_start()


class Switch(VGroup):
    """
    单刀单掷开关组件（中国高中教材标准样式）

    符号结构：
    - 两个接线柱（小圆圈）
    - 一个刀闸（线段）
    - 背景：黑色遮罩，确保遮挡网格线

    参数:
        wire_length: 引线长度，默认 0.5
        switch_length: 两个接线柱之间的距离（刀闸长度），默认 0.8
        is_closed: 初始状态，默认 False（断开）
        open_angle: 断开时的张角（弧度），默认 30 度
        color: 线条颜色，默认 WHITE
        stroke_width: 线条宽度，默认 4.0
    """

    def __init__(
        self,
        wire_length: float = 0.5,
        switch_length: float = 0.8,
        is_closed: bool = False,
        open_angle: float = 30 * DEGREES,
        color: str = WHITE,
        stroke_width: float = 4.0,
        **kwargs
    ):
        super().__init__(**kwargs)

        # 计算接线柱位置
        left_terminal_pos = LEFT * switch_length / 2
        right_terminal_pos = RIGHT * switch_length / 2

        # 计算总宽度（用于背景遮罩）
        total_width = 2 * wire_length + switch_length

        # Step 1: 创建背景遮罩（关键：遮挡网格线）
        mask_height = switch_length * 0.8
        background_mask = Rectangle(
            width=total_width,
            height=mask_height,
            stroke_color=BLACK,
            stroke_width=0,
            fill_color=BLACK,
            fill_opacity=1.0
        )
        background_mask.move_to(ORIGIN)
        background_mask.z_index = -10  # 最底层

        # Step 2: 创建引线
        # 左侧引线
        left_wire = Line(
            start=[-wire_length - switch_length/2, 0, 0],
            end=left_terminal_pos,
            color=color,
            stroke_width=stroke_width
        )
        left_wire.z_index = 0

        # 右侧引线
        right_wire = Line(
            start=right_terminal_pos,
            end=[wire_length + switch_length/2, 0, 0],
            color=color,
            stroke_width=stroke_width
        )
        right_wire.z_index = 0

        # Step 3: 创建接线柱（小圆圈）
        terminal_radius = 0.08

        left_terminal = Circle(
            radius=terminal_radius,
            color=color,
            stroke_width=stroke_width * 0.5,
            fill_color=BLACK,
            fill_opacity=1.0
        )
        left_terminal.move_to(left_terminal_pos)
        left_terminal.z_index = 10  # 顶层

        right_terminal = Circle(
            radius=terminal_radius,
            color=color,
            stroke_width=stroke_width * 0.5,
            fill_color=BLACK,
            fill_opacity=1.0
        )
        right_terminal.move_to(right_terminal_pos)
        right_terminal.z_index = 10  # 顶层

        # Step 4: 创建刀闸（关键：以左侧接线柱为旋转轴）
        # 先创建为水平状态（闭合状态）
        blade = Line(
            start=left_terminal_pos,
            end=right_terminal_pos,
            color=color,
            stroke_width=stroke_width
        )
        blade.z_index = 10  # 顶层

        # 根据 is_closed 参数决定刀闸状态
        if not is_closed:
            # 断开状态：刀闸抬起
            # 关键：以左侧接线柱中心为旋转点
            blade.rotate(
                angle=open_angle,
                about_point=left_terminal_pos
            )

        # Step 5: 组合所有元素（按 z-index 顺序添加）
        self.add(background_mask)
        self.add(left_wire, right_wire)
        self.add(left_terminal, right_terminal)
        self.add(blade)

        # 保存引用以便访问和动画
        self.background_mask = background_mask
        self.left_wire = left_wire
        self.right_wire = right_wire
        self.left_terminal = left_terminal
        self.right_terminal = right_terminal
        self.blade = blade
        self.switch_length = switch_length
        self.open_angle = open_angle
        self.is_closed = is_closed

    def get_left_terminal(self) -> np.ndarray:
        """
        获取左侧接线柱中心坐标

        Returns:
            左侧接线柱的三维坐标 [x, y, z]
        """
        return self.left_terminal.get_center()

    def get_right_terminal(self) -> np.ndarray:
        """
        获取右侧接线柱中心坐标

        Returns:
            右侧接线柱的三维坐标 [x, y, z]
        """
        return self.right_terminal.get_center()

    def get_left_wire_end(self) -> np.ndarray:
        """
        获取左侧引线的外端点坐标

        Returns:
            左侧引线外端点的三维坐标 [x, y, z]
        """
        return self.left_wire.get_start()

    def get_right_wire_end(self) -> np.ndarray:
        """
        获取右侧引线的外端点坐标

        Returns:
            右侧引线外端点的三维坐标 [x, y, z]
        """
        return self.right_wire.get_end()

    def close(self) -> Rotate:
        """
        闭合开关动画

        Returns:
            Rotate 动画对象，将刀闸从断开状态旋转到闭合状态
        """
        # 如果已经是闭合状态，返回空动画
        if self.is_closed:
            return Rotate(self.blade, 0, about_point=self.get_left_terminal())

        # 创建闭合动画：逆时针旋转 -open_angle（或顺时针旋转 open_angle，取决于方向）
        # 抬起是正角度，闭合需要负角度
        return Rotate(
            self.blade,
            angle=-self.open_angle,
            about_point=self.get_left_terminal()
        )

    def open(self) -> Rotate:
        """
        断开开关动画

        Returns:
            Rotate 动画对象，将刀闸从闭合状态旋转到断开状态
        """
        # 如果已经是断开状态，返回空动画
        if not self.is_closed:
            return Rotate(self.blade, 0, about_point=self.get_left_terminal())

        # 创建断开动画：顺时针旋转 open_angle
        return Rotate(
            self.blade,
            angle=self.open_angle,
            about_point=self.get_left_terminal()
        )

    def toggle(self) -> Rotate:
        """
        切换开关状态动画

        Returns:
            Rotate 动画对象，切换开关状态
        """
        if self.is_closed:
            return self.open()
        else:
            return self.close()


class Ammeter(VGroup):
    """
    电流表组件（中国高中教材标准样式）

    符号结构：
    - 圆形表盘（带黑色填充）
    - 中间字母 "A"
    - 左右引线（被圆圈遮挡内部部分）

    参数:
        radius: 仪表盘半径，默认 0.4
        wire_length: 左右引线长度，默认 0.5
        label_scale: 字母 A 的缩放比例，默认 0.7
        color: 线条颜色，默认 WHITE
        stroke_width: 线条宽度，默认 4.0
    """

    def __init__(
        self,
        radius: float = 0.4,
        wire_length: float = 0.5,
        label_scale: float = 0.7,
        color: str = WHITE,
        stroke_width: float = 4.0,
        **kwargs
    ):
        super().__init__(**kwargs)

        # Step 1: 创建左右引线
        # 左侧引线（从左边延伸到圆心）
        left_wire = Line(
            start=[-radius - wire_length, 0, 0],
            end=[0, 0, 0],  # 引线延伸到圆心，会被圆圈遮挡
            color=color,
            stroke_width=stroke_width
        )

        # 右侧引线（从圆心延伸到右边）
        right_wire = Line(
            start=[0, 0, 0],  # 从圆心开始，会被圆圈遮挡
            end=[radius + wire_length, 0, 0],
            color=color,
            stroke_width=stroke_width
        )

        # Step 2: 创建圆形表盘（关键：黑色填充会遮挡引线）
        circle = Circle(
            radius=radius,
            stroke_color=color,
            stroke_width=stroke_width,
            fill_color=BLACK,
            fill_opacity=1.0  # 完全不透明，遮挡内部引线
        )
        circle.move_to(ORIGIN)

        # Step 3: 创建字母 "A" 标签
        # 使用 Text 而不是 MathTex，更稳定
        label = Text(
            "A",
            font_size=48,
            color=WHITE,
            fill_opacity=1.0,
            stroke_width=0
        )
        label.move_to(ORIGIN)
        label.scale(label_scale)

        # Step 4: 按正确的 z-index 顺序添加到 VGroup
        # 关键：必须严格按照 wires -> circle -> label 的顺序添加
        self.add(left_wire)
        self.add(right_wire)
        self.add(circle)

        # 添加 label 后，立即设置其 z-index 为最上层
        self.add(label)

        # Step 5: 使用 set_z_index() 方法显式设置层级
        # 这是关键修复！必须使用方法而不是直接赋值
        left_wire.set_z_index(0)
        right_wire.set_z_index(0)
        circle.set_z_index(1)
        label.set_z_index(2)  # 确保字母在最上层

        # 保存引用以便访问
        self.left_wire = left_wire
        self.right_wire = right_wire
        self.circle = circle
        self.label = label
        self.radius = radius
        self.wire_length = wire_length

    def get_left_terminal(self) -> np.ndarray:
        """
        获取左侧接线端点坐标

        Returns:
            左侧引线外端点的三维坐标 [x, y, z]
        """
        return self.left_wire.get_start()

    def get_right_terminal(self) -> np.ndarray:
        """
        获取右侧接线端点坐标

        Returns:
            右侧引线外端点的三维坐标 [x, y, z]
        """
        return self.right_wire.get_end()


class Voltmeter(VGroup):
    """
    电压表组件（中国高中教材标准样式）

    符号结构：
    - 圆形表盘（带黑色填充）
    - 中间字母 "V"
    - 左右引线（被圆圈遮挡内部部分）

    参数:
        radius: 仪表盘半径，默认 0.4
        wire_length: 左右引线长度，默认 0.5
        label_scale: 字母 V 的缩放比例，默认 0.7
        color: 线条颜色，默认 WHITE
        stroke_width: 线条宽度，默认 4.0
    """

    def __init__(
        self,
        radius: float = 0.4,
        wire_length: float = 0.5,
        label_scale: float = 0.7,
        color: str = WHITE,
        stroke_width: float = 4.0,
        **kwargs
    ):
        super().__init__(**kwargs)

        # Step 1: 创建左右引线
        # 左侧引线（从左边延伸到圆心）
        left_wire = Line(
            start=[-radius - wire_length, 0, 0],
            end=[0, 0, 0],  # 引线延伸到圆心，会被圆圈遮挡
            color=color,
            stroke_width=stroke_width
        )

        # 右侧引线（从圆心延伸到右边）
        right_wire = Line(
            start=[0, 0, 0],  # 从圆心开始，会被圆圈遮挡
            end=[radius + wire_length, 0, 0],
            color=color,
            stroke_width=stroke_width
        )

        # Step 2: 创建圆形表盘（关键：黑色填充会遮挡引线）
        circle = Circle(
            radius=radius,
            stroke_color=color,
            stroke_width=stroke_width,
            fill_color=BLACK,
            fill_opacity=1.0  # 完全不透明，遮挡内部引线
        )
        circle.move_to(ORIGIN)

        # Step 3: 创建字母 "V" 标签
        # 使用 Text 而不是 MathTex，更稳定
        label = Text(
            "V",
            font_size=48,
            color=WHITE,
            fill_opacity=1.0,
            stroke_width=0
        )
        label.move_to(ORIGIN)
        label.scale(label_scale)

        # Step 4: 按正确的 z-index 顺序添加到 VGroup
        # 关键：必须严格按照 wires -> circle -> label 的顺序添加
        self.add(left_wire)
        self.add(right_wire)
        self.add(circle)

        # 添加 label 后，立即设置其 z-index 为最上层
        self.add(label)

        # Step 5: 使用 set_z_index() 方法显式设置层级
        # 这是关键修复！必须使用方法而不是直接赋值
        left_wire.set_z_index(0)
        right_wire.set_z_index(0)
        circle.set_z_index(1)
        label.set_z_index(2)  # 确保字母在最上层

        # 保存引用以便访问
        self.left_wire = left_wire
        self.right_wire = right_wire
        self.circle = circle
        self.label = label
        self.radius = radius
        self.wire_length = wire_length

    def get_left_terminal(self) -> np.ndarray:
        """
        获取左侧接线端点坐标

        Returns:
            左侧引线外端点的三维坐标 [x, y, z]
        """
        return self.left_wire.get_start()

    def get_right_terminal(self) -> np.ndarray:
        """
        获取右侧接线端点坐标

        Returns:
            右侧引线外端点的三维坐标 [x, y, z]
        """
        return self.right_wire.get_end()


class LightBulb(VGroup):
    """
    小灯泡组件（中国高中教材标准样式）

    符号结构：
    - 圆形灯泡主体（带黑色填充）
    - 内部 "X" 形交叉线（两条 Line 构建）
    - 左右引线（被圆圈遮挡内部部分）

    参数:
        radius: 灯泡半径，默认 0.5
        wire_length: 引线长度，默认 0.5
        stroke_width: 线条宽度，默认 4.0
        color: 线条颜色，默认 WHITE
    """

    def __init__(
        self,
        radius: float = 0.5,
        wire_length: float = 0.5,
        stroke_width: float = 4.0,
        color: str = WHITE,
        **kwargs
    ):
        super().__init__(**kwargs)

        # Step 1: 创建左右引线
        left_wire = Line(
            start=[-radius - wire_length, 0, 0],
            end=[0, 0, 0],
            color=color,
            stroke_width=stroke_width
        )

        right_wire = Line(
            start=[0, 0, 0],
            end=[radius + wire_length, 0, 0],
            color=color,
            stroke_width=stroke_width
        )

        # Step 2: 创建圆形灯泡主体
        body = Circle(
            radius=radius,
            stroke_color=color,
            stroke_width=stroke_width,
            fill_color=BLACK,
            fill_opacity=1.0
        )
        body.move_to(ORIGIN)

        # Step 3: 创建 "X" 形交叉线
        cross_length = radius * 2 * 0.7

        cross1 = Line(
            start=[-cross_length/2, 0, 0],
            end=[cross_length/2, 0, 0],
            color=color,
            stroke_width=stroke_width
        )
        cross1.rotate(45 * DEGREES, about_point=ORIGIN)

        cross2 = Line(
            start=[-cross_length/2, 0, 0],
            end=[cross_length/2, 0, 0],
            color=color,
            stroke_width=stroke_width
        )
        cross2.rotate(-45 * DEGREES, about_point=ORIGIN)

        cross = VGroup(cross1, cross2)
        cross.move_to(ORIGIN)

        # Step 4: 添加到 VGroup
        self.add(left_wire)
        self.add(right_wire)
        self.add(body)
        self.add(cross)

        # Step 5: 设置 z-index
        left_wire.set_z_index(0)
        right_wire.set_z_index(0)
        body.set_z_index(1)
        cross.set_z_index(2)

        # 保存引用
        self.left_wire = left_wire
        self.right_wire = right_wire
        self.body = body
        self.cross = cross
        self.radius = radius
        self.wire_length = wire_length

    def get_left_terminal(self) -> np.ndarray:
        return self.left_wire.get_start()

    def get_right_terminal(self) -> np.ndarray:
        return self.right_wire.get_end()


class Capacitor(VGroup):
    """
    平行板电容器组件（中国高中教材标准样式）

    符号结构：
    - 两条平行的等长竖直线（极板）
    - 背景：黑色遮罩，确保遮挡网格线
    - 左右引线

    参数:
        height: 极板高度，默认 0.8（两板等高）
        plate_spacing: 两板间距，默认 0.3
        wire_length: 引线长度，默认 0.5
        color: 线条颜色，默认 WHITE
        stroke_width: 线条宽度，默认 4.0
    """

    def __init__(
        self,
        height: float = 0.8,
        plate_spacing: float = 0.3,
        wire_length: float = 0.5,
        color: str = WHITE,
        stroke_width: float = 4.0,
        **kwargs
    ):
        super().__init__(**kwargs)

        # 计算组件总宽度（用于背景遮罩）
        total_width = 2 * wire_length + plate_spacing

        # Step 1: 创建背景遮罩（关键：遮挡网格线）
        # 高度略大于极板，确保完全覆盖
        mask_height = height * 1.5
        background_mask = Rectangle(
            width=total_width,
            height=mask_height,
            stroke_color=BLACK,
            stroke_width=0,
            fill_color=BLACK,
            fill_opacity=1.0
        )
        background_mask.move_to(ORIGIN)
        background_mask.z_index = -10  # 最底层（遮罩）

        # Step 2: 创建左右引线
        # 左侧引线
        left_wire = Line(
            start=[-wire_length - plate_spacing/2, 0, 0],
            end=[-plate_spacing/2, 0, 0],
            color=color,
            stroke_width=stroke_width
        )
        left_wire.z_index = 0

        # 右侧引线
        right_wire = Line(
            start=[plate_spacing/2, 0, 0],
            end=[wire_length + plate_spacing/2, 0, 0],
            color=color,
            stroke_width=stroke_width
        )
        right_wire.z_index = 0

        # Step 3: 创建左右极板（等高竖直线）
        # 左极板
        left_plate = Line(
            start=[-plate_spacing/2, -height/2, 0],
            end=[-plate_spacing/2, height/2, 0],
            color=color,
            stroke_width=stroke_width
        )
        left_plate.z_index = 10  # 顶层（极板）

        # 右极板（与左板等高）
        right_plate = Line(
            start=[plate_spacing/2, -height/2, 0],
            end=[plate_spacing/2, height/2, 0],
            color=color,
            stroke_width=stroke_width
        )
        right_plate.z_index = 10  # 顶层（极板）

        # Step 4: 按正确的 z-index 顺序添加到 VGroup
        self.add(background_mask)  # 最底层（遮罩）
        self.add(left_wire)        # 中间层（引线）
        self.add(right_wire)
        self.add(left_plate)       # 最顶层（极板）
        self.add(right_plate)

        # 保存引用以便访问
        self.background_mask = background_mask
        self.left_wire = left_wire
        self.right_wire = right_wire
        self.left_plate = left_plate
        self.right_plate = right_plate
        self.height = height
        self.plate_spacing = plate_spacing
        self.wire_length = wire_length

    def get_left_terminal(self) -> np.ndarray:
        """
        获取左侧接线端点坐标

        Returns:
            左侧引线外端点的三维坐标 [x, y, z]
        """
        return self.left_wire.get_start()

    def get_right_terminal(self) -> np.ndarray:
        """
        获取右侧接线端点坐标

        Returns:
            右侧引线外端点的三维坐标 [x, y, z]
        """
        return self.right_wire.get_end()


class Rheostat(VGroup):
    """
    滑动变阻器组件（中国高中教材标准样式）

    符号结构：
    - 长方形电阻主体（黑色填充）
    - 左端接线柱 (A)、右端接线柱 (B)
    - 滑动端接线柱 (C) 位于上方
    - 滑片：折线 + 箭头，箭头指向电阻上边缘
    - 滑片位置由 alpha 参数控制（0.0=最左，1.0=最右）

    参数:
        body_width: 电阻主体宽度，默认 2.0
        body_height: 电阻主体高度，默认 0.5
        handle_height: 滑轨高度（电阻顶部到接线柱 C），默认 0.8
        alpha: 滑片位置，默认 0.5（居中）
        wire_length: 左右引线长度，默认 0.5
        terminal_radius: 接线柱半径，默认 0.08
        color: 线条颜色，默认 WHITE
        stroke_width: 线条宽度，默认 4.0
    """

    def __init__(
        self,
        body_width: float = 2.0,
        body_height: float = 0.5,
        handle_height: float = 0.8,
        alpha: float = 0.5,
        wire_length: float = 0.5,
        terminal_radius: float = 0.08,
        color: str = WHITE,
        stroke_width: float = 4.0,
        **kwargs
    ):
        super().__init__(**kwargs)

        # 计算主体几何参数
        body_left = -body_width / 2
        body_right = body_width / 2
        body_top = body_height / 2
        body_bottom = -body_height / 2

        # Step 1: 创建电阻主体（长方形，黑色填充）
        body = Rectangle(
            width=body_width,
            height=body_height,
            stroke_color=color,
            stroke_width=stroke_width,
            fill_color=BLACK,
            fill_opacity=1.0
        )
        body.move_to(ORIGIN)
        body.z_index = 0

        # Step 2: 创建左右引线
        # 左侧引线（接线柱 A）
        left_wire = Line(
            start=[body_left - wire_length, 0, 0],
            end=[body_left, 0, 0],
            color=color,
            stroke_width=stroke_width
        )
        left_wire.z_index = 0

        # 右侧引线（接线柱 B）
        right_wire = Line(
            start=[body_right, 0, 0],
            end=[body_right + wire_length, 0, 0],
            color=color,
            stroke_width=stroke_width
        )
        right_wire.z_index = 0

        # Step 3: 创建三个接线柱（小圆圈）
        # 接线柱 A（左端）
        terminal_a = Circle(
            radius=terminal_radius,
            color=color,
            stroke_width=stroke_width * 0.5,
            fill_color=BLACK,
            fill_opacity=1.0
        )
        terminal_a.move_to([body_left - wire_length, 0, 0])
        terminal_a.z_index = 10

        # 接线柱 B（右端）
        terminal_b = Circle(
            radius=terminal_radius,
            color=color,
            stroke_width=stroke_width * 0.5,
            fill_color=BLACK,
            fill_opacity=1.0
        )
        terminal_b.move_to([body_right + wire_length, 0, 0])
        terminal_b.z_index = 10

        # Step 4: 计算滑片位置
        # 限制 alpha 在 [0, 1] 范围内
        alpha = max(0.0, min(1.0, alpha))
        contact_x = body_left + alpha * body_width
        contact_point = np.array([contact_x, body_top, 0])

        # 垂直线顶部（滑轨高度）
        vertical_top = np.array([contact_x, body_top + handle_height, 0])

        # 接线柱 C 位置（右上角上方）
        terminal_c_pos = np.array([body_right, body_top + handle_height, 0])

        # Step 5: 创建滑片结构
        # 垂直线（从箭头顶部向上）
        vertical_wire = Line(
            start=contact_point,
            end=vertical_top,
            color=color,
            stroke_width=stroke_width
        )
        vertical_wire.z_index = 10

        # 水平线（从垂直线顶部到接线柱 C）
        horizontal_wire = Line(
            start=vertical_top,
            end=terminal_c_pos,
            color=color,
            stroke_width=stroke_width
        )
        horizontal_wire.z_index = 10

        # 箭头（指向电阻主体）
        # 关键：箭头尖端刚好抵在电阻上边缘，不穿过
        arrow_size = 0.12
        arrow_height = arrow_size * 1.5

        arrow = Polygon(
            [contact_point[0] - arrow_size, contact_point[1] + arrow_height, 0],  # 左上角
            [contact_point[0] + arrow_size, contact_point[1] + arrow_height, 0],  # 右上角
            [contact_point[0], contact_point[1], 0],  # 尖端（刚好在 body_top）
            color=color,
            stroke_width=stroke_width * 0.8
        )
        arrow.set_fill(BLACK, opacity=1.0)
        arrow.z_index = 10

        # 接线柱 C（滑动端）
        terminal_c = Circle(
            radius=terminal_radius,
            color=color,
            stroke_width=stroke_width * 0.5,
            fill_color=BLACK,
            fill_opacity=1.0
        )
        terminal_c.move_to(terminal_c_pos)
        terminal_c.z_index = 10

        # Step 6: 组合所有元素
        self.add(body)
        self.add(left_wire, right_wire)
        self.add(terminal_a, terminal_b, terminal_c)
        self.add(vertical_wire, horizontal_wire)
        self.add(arrow)

        # 保存引用以便访问
        self.body = body
        self.left_wire = left_wire
        self.right_wire = right_wire
        self.terminal_a = terminal_a
        self.terminal_b = terminal_b
        self.terminal_c = terminal_c
        self.vertical_wire = vertical_wire
        self.horizontal_wire = horizontal_wire
        self.arrow = arrow
        self.body_width = body_width
        self.body_height = body_height
        self.handle_height = handle_height
        self.wire_length = wire_length
        self.alpha = alpha
        self.terminal_radius = terminal_radius

    def get_terminal_a(self) -> np.ndarray:
        """
        获取左端接线柱 (A) 中心坐标

        Returns:
            接线柱 A 的三维坐标 [x, y, z]
        """
        return self.terminal_a.get_center()

    def get_terminal_b(self) -> np.ndarray:
        """
        获取右端接线柱 (B) 中心坐标

        Returns:
            接线柱 B 的三维坐标 [x, y, z]
        """
        return self.terminal_b.get_center()

    def get_terminal_c(self) -> np.ndarray:
        """
        获取滑动端接线柱 (C) 中心坐标

        Returns:
            接线柱 C 的三维坐标 [x, y, z]
        """
        return self.terminal_c.get_center()

    def change_value(self, new_alpha: float):
        """
        更新滑片位置

        参数:
            new_alpha: 新的滑片位置，范围 [0.0, 1.0]
        """
        # 限制 alpha 在 [0, 1] 范围内
        new_alpha = max(0.0, min(1.0, new_alpha))
        self.alpha = new_alpha

        # 重新计算位置
        body_left = -self.body_width / 2
        body_top = self.body_height / 2
        contact_x = body_left + new_alpha * self.body_width
        contact_point = np.array([contact_x, body_top, 0])
        vertical_top = np.array([contact_x, body_top + self.handle_height, 0])
        terminal_c_pos = np.array([self.body_width / 2, body_top + self.handle_height, 0])

        # 更新垂直线
        self.vertical_wire.put_start_and_end_on(contact_point, vertical_top)

        # 更新水平线
        self.horizontal_wire.put_start_and_end_on(vertical_top, terminal_c_pos)

        # 更新箭头位置
        arrow_size = 0.12
        arrow_height = arrow_size * 1.5
        self.arrow.set_points_as_corners([
            [contact_x - arrow_size, body_top + arrow_height, 0],  # 左上角
            [contact_x + arrow_size, body_top + arrow_height, 0],  # 右上角
            [contact_x, body_top, 0]  # 尖端（刚好在 body_top）
        ])

        # 更新接线柱 C 位置（虽然它不动，但保持一致）
        self.terminal_c.move_to(terminal_c_pos)


class Potentiometer(VGroup):
    """
    电位器组件（中国高中教材标准样式）

    符号结构：
    - 长方形电阻主体（黑色填充）
    - 斜向穿透箭头（从左下到右上，45度）
    - 箭头位于主体上层，保留完整穿透效果

    参数:
        body_width: 电阻主体宽度，默认 1.2
        body_height: 电阻主体高度，默认 0.4
        wire_length: 引线长度，默认 0.5
        arrow_scale: 箭头长度相对于对角线的倍数，默认 1.5
        arrow_angle: 箭头角度（从左下到右上），默认 45 度
        color: 线条颜色，默认 WHITE
        stroke_width: 线条宽度，默认 4.0
    """

    def __init__(
        self,
        body_width: float = 1.2,
        body_height: float = 0.4,
        wire_length: float = 0.5,
        arrow_scale: float = 1.5,
        arrow_angle: float = 45 * DEGREES,
        color: str = WHITE,
        stroke_width: float = 4.0,
        **kwargs
    ):
        super().__init__(**kwargs)

        # Step 1: 创建电阻主体（长方形，黑色填充）
        body = Rectangle(
            width=body_width,
            height=body_height,
            stroke_color=color,
            stroke_width=stroke_width,
            fill_color=BLACK,
            fill_opacity=1.0
        )
        body.move_to(ORIGIN)
        body.z_index = 0  # 底层（主体）

        # Step 2: 创建左右引线
        # 左侧引线
        left_wire = Line(
            start=[-body_width/2 - wire_length, 0, 0],
            end=[-body_width/2, 0, 0],
            color=color,
            stroke_width=stroke_width
        )
        left_wire.z_index = 0

        # 右侧引线
        right_wire = Line(
            start=[body_width/2, 0, 0],
            end=[body_width/2 + wire_length, 0, 0],
            color=color,
            stroke_width=stroke_width
        )
        right_wire.z_index = 0

        # Step 3: 创建斜向穿透箭头
        # 计算电阻对角线长度
        diagonal_length = np.sqrt(body_width**2 + body_height**2)
        
        # 箭头长度为对角线的 arrow_scale 倍
        arrow_length = diagonal_length * arrow_scale

        # 创建箭头（初始为水平）
        arrow = Arrow(
            start=LEFT * arrow_length / 2,
            end=RIGHT * arrow_length / 2,
            buff=0,
            stroke_width=stroke_width,
            color=color,
            max_tip_length_to_length_ratio=0.15  # 控制箭头尖大小
        )

        # 旋转箭头并居中
        arrow.rotate(arrow_angle, about_point=ORIGIN)
        arrow.move_to(ORIGIN)
        arrow.z_index = 10  # 顶层（箭头），确保在主体之上

        # Step 4: 按正确的 z-index 顺序添加到 VGroup
        # 顺序：引线（底层） -> 主体（中层） -> 箭头（顶层）
        self.add(left_wire)
        self.add(right_wire)
        self.add(body)
        self.add(arrow)

        # 再次确保 z-index 正确（使用 set_z_index 方法）
        left_wire.set_z_index(0)
        right_wire.set_z_index(0)
        body.set_z_index(1)
        arrow.set_z_index(2)  # 箭头在最上层，保留完整穿透效果

        # 保存引用以便访问
        self.left_wire = left_wire
        self.right_wire = right_wire
        self.body = body
        self.arrow = arrow
        self.body_width = body_width
        self.body_height = body_height
        self.wire_length = wire_length

    def get_left_terminal(self) -> np.ndarray:
        """
        获取左侧接线端点坐标

        Returns:
            左侧引线外端点的三维坐标 [x, y, z]
        """
        return self.left_wire.get_start()

    def get_right_terminal(self) -> np.ndarray:
        """
        获取右侧接线端点坐标

        Returns:
            右侧引线外端点的三维坐标 [x, y, z]
        """
        return self.right_wire.get_end()


class Inductor(VGroup):
    """
    电感器组件（中国高中教材标准样式）

    符号结构：
    - 多个连续的半圆弧线圈（波浪形状）
    - 背景遮罩：黑色填充，遮挡网格线
    - 左右引线

    参数:
        num_loops: 线圈圈数，默认 4
        radius: 每个半圆的半径，默认 0.2
        wire_length: 左右引线长度，默认 0.5
        color: 线条颜色，默认 WHITE
        stroke_width: 线条宽度，默认 4.0
    """

    def __init__(
        self,
        num_loops: int = 4,
        radius: float = 0.2,
        wire_length: float = 0.5,
        color: str = WHITE,
        stroke_width: float = 4.0,
        **kwargs
    ):
        super().__init__(**kwargs)

        # 计算线圈总宽度
        coil_width = num_loops * 2 * radius
        coil_height = radius * 2  # 半圆的直径

        # Step 1: 创建线圈（多个连续的半圆弧）
        coils = VGroup()

        for i in range(num_loops):
            # 创建标准向上凸起的半圆弧（拱门形状）
            # start_angle=PI (180度，左侧), angle=-PI (-180度，逆时针画上半圆到右侧)
            arc = Arc(
                radius=radius,
                start_angle=PI,
                angle=-PI,
                color=color,
                stroke_width=stroke_width
            )

            # 关键：每个半圆只是简单地向右平移直径的距离
            # 第 i 个半圆向右平移 i * 2 * radius
            arc.shift(RIGHT * (i * 2 * radius))
            coils.add(arc)

        # 将线圈整体居中
        coils.move_to(ORIGIN)

        # Step 2: 创建背景遮罩（关键：遮挡网格线）
        background_mask = Rectangle(
            width=coil_width,
            height=coil_height,
            stroke_color=BLACK,
            stroke_width=0,
            fill_color=BLACK,
            fill_opacity=1.0
        )
        background_mask.move_to(ORIGIN)
        background_mask.z_index = -10  # 最底层

        # Step 3: 创建左右引线
        # 计算线圈的左端点和右端点
        # 左端点：第一个半圆的起点（最左侧）
        coil_left_x = -coil_width / 2
        coil_right_x = coil_width / 2

        # 左侧引线
        left_wire = Line(
            start=[coil_left_x - wire_length, 0, 0],
            end=[coil_left_x, 0, 0],
            color=color,
            stroke_width=stroke_width
        )
        left_wire.z_index = 0

        # 右侧引线
        right_wire = Line(
            start=[coil_right_x, 0, 0],
            end=[coil_right_x + wire_length, 0, 0],
            color=color,
            stroke_width=stroke_width
        )
        right_wire.z_index = 0

        # Step 4: 设置线圈的 z-index
        coils.set_z_index(0)

        # Step 5: 按正确的 z-index 顺序添加到 VGroup
        # 顺序：遮罩（最底层） -> 引线 -> 线圈
        self.add(background_mask)
        self.add(left_wire)
        self.add(right_wire)
        self.add(coils)

        # 再次确保 z-index 正确
        background_mask.set_z_index(-10)
        left_wire.set_z_index(0)
        right_wire.set_z_index(0)
        coils.set_z_index(0)

        # 保存引用以便访问
        self.background_mask = background_mask
        self.left_wire = left_wire
        self.right_wire = right_wire
        self.coils = coils
        self.num_loops = num_loops
        self.radius = radius
        self.coil_width = coil_width
        self.coil_height = coil_height
        self.wire_length = wire_length

    def get_left_terminal(self) -> np.ndarray:
        """
        获取左侧接线端点坐标

        Returns:
            左侧引线外端点的三维坐标 [x, y, z]
        """
        return self.left_wire.get_start()

    def get_right_terminal(self) -> np.ndarray:
        """
        获取右侧接线端点坐标

        Returns:
            右侧引线外端点的三维坐标 [x, y, z]
        """
        return self.right_wire.get_end()


class LED(VGroup):
    """
    发光二极管组件（Light Emitting Diode，中国高中教材标准样式）

    符号结构：
    - 向右指的正三角形主体（等边三角形，黑色填充）
    - 右侧垂直截止线
    - 上方两个发射箭头（指向左上方/西北方向，相互平行且分离）
    - 左右水平引线

    参数:
        side_length: 正三角形边长，默认 1.2（增大尺寸）
        wire_length: 引线长度，默认 0.8
        arrow_size: 发射箭头长度，默认 0.6
        arrow_offset: 箭头平移偏移量，默认 (0.25, 0.15)
        color: 线条颜色，默认 WHITE
        stroke_width: 线条宽度，默认 4.0
    """

    def __init__(
        self,
        side_length: float = 1.2,
        wire_length: float = 0.8,
        arrow_size: float = 0.6,
        arrow_offset: tuple = (0.25, 0.15),
        color: str = WHITE,
        stroke_width: float = 4.0,
        **kwargs
    ):
        super().__init__(**kwargs)

        # Step 1: 创建正三角形主体（向右指）
        # 正三角形高度公式：h = a * sqrt(3) / 2
        height = side_length * np.sqrt(3) / 2

        # 三角形顶点（居中）
        # 左边（底边）垂直，右顶点指向右侧
        left_top = np.array([-side_length/2, height/2, 0])
        left_bottom = np.array([-side_length/2, -height/2, 0])
        right_tip = np.array([side_length/2, 0, 0])

        triangle = Polygon(
            left_top,
            left_bottom,
            right_tip,
            stroke_color=color,
            stroke_width=stroke_width,
            fill_color=BLACK,
            fill_opacity=1.0  # 黑色填充，遮挡背景
        )
        triangle.z_index = 0

        # Step 2: 创建右侧垂直截止线
        bar_height = height * 1.1  # 稍高于三角形
        vertical_bar = Line(
            start=[side_length/2, -bar_height/2, 0],
            end=[side_length/2, bar_height/2, 0],
            color=color,
            stroke_width=stroke_width
        )
        vertical_bar.z_index = 0

        # Step 3: 创建第一个发射箭头（指向西北方向）
        # 西北方向角度：135度（从x轴正方向逆时针）
        arrow_angle = 135 * DEGREES

        # 第一个箭头位置（在三角形上方偏左位置）
        arrow1_center = np.array([
            -0.1,  # 稍微偏左
            height/2 + 0.3,  # 三角形上方
            0
        ])

        arrow1 = Arrow(
            start=arrow1_center - LEFT * arrow_size/2,
            end=arrow1_center + LEFT * arrow_size/2,
            buff=0,
            stroke_width=stroke_width * 0.8,
            color=color,
            max_tip_length_to_length_ratio=0.25
        )

        # 旋转到西北方向
        arrow1.rotate(arrow_angle - PI, about_point=arrow1_center)

        # Step 4: 通过复制+平移创建第二个箭头（保证绝对平行）
        arrow2 = arrow1.copy()
        # 向右上方平移
        arrow2.shift(RIGHT * arrow_offset[0] + UP * arrow_offset[1])

        # 组合箭头
        arrows = VGroup(arrow1, arrow2)
        arrows.z_index = 10

        # Step 5: 创建左右引线
        # 左侧引线（连接到三角形底边中心）
        left_wire = Line(
            start=[-side_length/2 - wire_length, 0, 0],
            end=[-side_length/2, 0, 0],
            color=color,
            stroke_width=stroke_width
        )
        left_wire.z_index = 0

        # 右侧引线（连接到垂直截止线）
        right_wire = Line(
            start=[side_length/2, 0, 0],
            end=[side_length/2 + wire_length, 0, 0],
            color=color,
            stroke_width=stroke_width
        )
        right_wire.z_index = 0

        # Step 6: 组合所有元素
        self.add(triangle)
        self.add(vertical_bar)
        self.add(arrows)
        self.add(left_wire)
        self.add(right_wire)

        # 设置 z-index
        triangle.set_z_index(0)
        vertical_bar.set_z_index(0)
        arrows.set_z_index(10)
        left_wire.set_z_index(0)
        right_wire.set_z_index(0)

        # 保存引用以便访问
        self.triangle = triangle
        self.vertical_bar = vertical_bar
        self.arrows = arrows
        self.arrow1 = arrow1
        self.arrow2 = arrow2
        self.left_wire = left_wire
        self.right_wire = right_wire
        self.side_length = side_length
        self.height = height
        self.wire_length = wire_length

    def get_left_terminal(self) -> np.ndarray:
        """
        获取左侧接线端点坐标

        Returns:
            左侧引线外端点的三维坐标 [x, y, z]
        """
        return self.left_wire.get_start()

    def get_right_terminal(self) -> np.ndarray:
        """
        获取右侧接线端点坐标

        Returns:
            右侧引线外端点的三维坐标 [x, y, z]
        """
        return self.right_wire.get_end()
