"""
斜二测正方体组件 - Oblique Cube Geometry

实现中国高中数学教材标准的斜二测画法（Oblique Projection）。

坐标定义：
- u_x: 深度轴，指向屏幕左下方 45°
- u_y: 水平轴，指向屏幕右侧
- u_z: 竖直轴，指向屏幕上方

作者: Manim 数学组件库
日期: 2026-02-15
"""

from __future__ import annotations

import numpy as np
from manim import *
from typing import Dict, Tuple, Optional


class ObliqueCube(VGroup):
    """
    斜二测正方体组件（纯 2D 投影）

    特性：
    - 标准 45° 斜二测画法
    - 缩短系数 0.5（可配置）
    - 手动虚实线控制
    - 手动标签布局（避免遮挡）
    - 完全可预测的输出

    参数：
    -------
    side_length : float
        正方体边长
    shortening_factor : float
        斜二测缩短系数（默认 0.5）
    angle : float
        倾斜角度（弧度，默认 PI/4 = 45°）
    show_axes : bool
        是否显示坐标轴
    show_labels : bool
        是否显示顶点标签
    origin_offset : np.ndarray
        原点偏移（用于居中，默认 LEFT * 2 + DOWN * 1）
    **kwargs
        其他 VGroup 参数
    """

    def __init__(
        self,
        side_length: float = 2.5,
        shortening_factor: float = 0.5,
        angle: float = PI / 4,
        show_axes: bool = True,
        show_labels: bool = True,
        origin_offset: np.ndarray = None,
        **kwargs
    ):
        super().__init__(**kwargs)

        self.side_length = side_length
        self.shortening_factor = shortening_factor
        self.angle = angle
        self.show_axes = show_axes
        self.show_labels = show_labels

        # 默认原点偏移（居中）
        if origin_offset is None:
            origin_offset = LEFT * 2 + DOWN * 1
        self.origin_offset = origin_offset

        # 定义 8 个顶点（用户坐标）
        self.vertices_user = {
            "A":  (0, 0, 0),
            "B":  (side_length, 0, 0),   # u_x 轴（深度，左下）
            "D":  (0, side_length, 0),   # u_y 轴（水平，向右）
            "C":  (side_length, side_length, 0),   # (u_x, u_y)
            "A1": (0, 0, side_length),   # u_z 轴（竖直，向上）
            "B1": (side_length, 0, side_length),   # (u_x, u_z)
            "D1": (0, side_length, side_length),   # (u_y, u_z)
            "C1": (side_length, side_length, side_length),   # (u_x, u_y, u_z)
        }

        # 计算屏幕坐标
        self.vertices_screen = self._project_all_vertices()

        # 创建坐标轴
        if show_axes:
            self._create_axes()

        # 创建棱边
        self._create_edges()

        # 创建标签
        if show_labels:
            self._create_labels()

    def _project(self, u_x: float, u_y: float, u_z: float) -> np.ndarray:
        """
        斜二测投影函数

        将用户坐标系投影到屏幕坐标

        参数：
        - u_x: 深度轴（左下 45°）
        - u_y: 水平轴（向右）
        - u_z: 竖直轴（向上）

        返回：
        - np.array([screen_x, screen_y, 0])
        """
        v = self.shortening_factor
        alpha = self.angle

        # 斜二测投影公式
        screen_x = u_y - u_x * v * np.cos(alpha)
        screen_y = u_z - u_x * v * np.sin(alpha)

        # 原点偏移
        return np.array([screen_x, screen_y, 0]) + self.origin_offset

    def _project_all_vertices(self) -> Dict[str, np.ndarray]:
        """计算所有顶点的屏幕坐标"""
        vertices_screen = {}
        for name, (ux, uy, uz) in self.vertices_user.items():
            vertices_screen[name] = self._project(ux, uy, uz)
        return vertices_screen

    def _create_axes(self):
        """创建坐标轴"""
        L = self.side_length

        # x 轴（u_x，深度，左下 45°）
        x_axis = Arrow(
            start=self.vertices_screen["A"],
            end=self._project(L * 1.5, 0, 0),
            color=RED_E,
            buff=0,
            max_stroke_width_to_length_ratio=0.05
        )
        x_label = MathTex("x", font_size=24, color=RED_E)
        x_label.move_to(self._project(L * 1.7, 0, 0))

        # y 轴（u_y，水平，向右）
        y_axis = Arrow(
            start=self.vertices_screen["A"],
            end=self._project(0, L * 1.5, 0),
            color=GREEN_E,
            buff=0,
            max_stroke_width_to_length_ratio=0.05
        )
        y_label = MathTex("y", font_size=24, color=GREEN_E)
        y_label.move_to(self._project(0, L * 1.7, 0))

        # z 轴（u_z，竖直，向上）
        z_axis = Arrow(
            start=self.vertices_screen["A"],
            end=self._project(0, 0, L * 1.5),
            color=BLUE_E,
            buff=0,
            max_stroke_width_to_length_ratio=0.05
        )
        z_label = MathTex("z", font_size=24, color=BLUE_E)
        z_label.move_to(self._project(0, 0, L * 1.7))

        self.axes = VGroup(x_axis, x_label, y_axis, y_label, z_axis, z_label)
        self.add(self.axes)

    def _create_edges(self):
        """创建棱边"""
        self.edges = VGroup()

        # 虚线（从原点 A 发散的三条棱，被遮挡）
        dashed_edges = [
            ("A", "B"),   # u_x 方向
            ("A", "D"),   # u_y 方向
            ("A", "A1"),  # u_z 方向
        ]

        for v1_name, v2_name in dashed_edges:
            line = DashedLine(
                start=self.vertices_screen[v1_name],
                end=self.vertices_screen[v2_name],
                color=GRAY,
                stroke_width=3,
                dash_length=0.15,
                stroke_opacity=0.6
            )
            self.edges.add(line)

        # 实线（其余 9 条棱）
        solid_edges = [
            ("B", "C"), ("C", "D"),      # 底面剩余边
            ("A1", "B1"), ("B1", "C1"), ("C1", "D1"), ("D1", "A1"),  # 顶面
            ("B", "B1"), ("C", "C1"), ("D", "D1"),  # 竖棱
        ]

        for v1_name, v2_name in solid_edges:
            line = Line(
                start=self.vertices_screen[v1_name],
                end=self.vertices_screen[v2_name],
                color=WHITE,
                stroke_width=3
            )
            self.edges.add(line)

        self.add(self.edges)

    def _create_labels(self):
        """创建顶点标签（手动偏移映射表）"""
        # 定义偏移字典（方向向量）
        label_offsets = {
            "A":  (LEFT + DOWN) * 0.8,     # 原点：左下（避开 XYZ 轴）
            "B":  DOWN,                     # X 轴尖端：向下（避开 X 轴箭头）
            "C":  DOWN + RIGHT,             # 右下角：右下
            "D":  DOWN,                     # Y 轴尖端：向下（避开 Y 轴箭头）
            "A1": LEFT,                     # Z 轴尖端：向左（避开 Z 轴箭头）
            "B1": LEFT,                     # 左上角：向左
            "C1": UP + RIGHT,              # 右上角：右上
            "D1": UP                        # 后上角：向上
        }

        # 紧凑距离参数
        default_buff = 0.25

        self.labels = VGroup()
        for name, pos in self.vertices_screen.items():
            if "1" in name:
                base_name = name[0]
                label = MathTex(base_name + "_1", font_size=28, color=YELLOW)
            else:
                label = MathTex(name, font_size=28, color=YELLOW)

            # 获取对应的偏移方向
            direction = label_offsets.get(name, UP)

            # 应用偏移
            label_pos = pos + direction * default_buff
            label.move_to(label_pos)

            self.labels.add(label)

        self.add(self.labels)

    def get_vertex_position(self, vertex_name: str) -> np.ndarray:
        """
        获取指定顶点的屏幕坐标

        参数：
        - vertex_name: 顶点名称（"A", "B", "C", ...）

        返回：
        - np.ndarray: 屏幕坐标
        """
        return self.vertices_screen.get(vertex_name, ORIGIN)

    def get_all_vertices(self) -> Dict[str, np.ndarray]:
        """获取所有顶点的屏幕坐标"""
        return self.vertices_screen.copy()
