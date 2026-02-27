"""
正方体组件 - Cube Geometry

实现标准正方体的可视化，符合中国高中数学教材风格。

作者: Manim 数学组件库
日期: 2026-02-15
"""

from __future__ import annotations

import numpy as np
from manim import *
from typing import Optional, List

from .solid_base import PolyhedronBase


class CubeGeometry(PolyhedronBase):
    """
    正方体组件

    坐标系定义：
    - 原点固定在顶点 A (0,0,0)
    - x 轴正方向：沿棱 AB 方向
    - y 轴正方向：沿棱 AD 方向
    - z 轴正方向：沿棱 AA1 方向

    特性：
    - 标签与几何体解耦（不继承旋转）
    - 使用隐藏的 Dot 作为顶点锚点
    - 提供 get_global_vertices() 获取当前顶点的全局坐标
    - 自动虚实线渲染（根据相机位置）
    """

    def __init__(
        self,
        side_length: float = 2.0,
        origin_point: str = "A",
        show_axes: bool = True,
        show_labels: bool = True,
        axes_length: float = 3.0,
        **kwargs
    ):
        self.side_length = side_length
        self.origin_point = origin_point.upper()
        self.show_axes = show_axes
        self.show_labels = show_labels
        self.axes_length = axes_length

        L = side_length

        # 标准顶点坐标（以 A 为原点）
        self.standard_vertices = {
            "A":  np.array([0, 0, 0]),
            "B":  np.array([L, 0, 0]),
            "D":  np.array([0, L, 0]),
            "C":  np.array([L, L, 0]),
            "A1": np.array([0, 0, L]),
            "B1": np.array([L, 0, L]),
            "D1": np.array([0, L, L]),
            "C1": np.array([L, L, L]),
        }

        # 顶点名称列表
        self.vertex_names = ["A", "B", "C", "D", "A1", "B1", "C1", "D1"]

        # 计算偏移量
        offset = -self.standard_vertices[self.origin_point]

        # 应用偏移并创建顶点列表
        vertices = []
        for name in self.vertex_names:
            vertices.append(self.standard_vertices[name] + offset)

        # 定义面（顶点顺序待校正）
        faces = [
            [0, 1, 2, 3],  # 底面 A-B-C-D（或A-B-C-D？待校正）
            [4, 5, 6, 7],  # 顶面 A1-B1-C1-D1
            [0, 1, 5, 4],  # 前面 A-B-B1-A1
            [1, 2, 6, 5],  # 右面 B-C-C1-B1
            [2, 3, 7, 6],  # 后面 C-D-D1-C1
            [3, 0, 4, 7],  # 左面 D-A-A1-D1
        ]

        # ============================
        # 法线自动校正（防御性编程）
        # ============================
        faces = self._correct_face_normals(vertices, faces)

        # 初始化基类
        super().__init__(vertices=vertices, faces=faces, **kwargs)

        # ============================
        # 创建隐藏的顶点锚点（用于追踪顶点位置）
        # ============================
        self._vertex_anchors = VGroup()
        for vertex in vertices:
            anchor = Dot(point=vertex, radius=0.01, fill_opacity=0, stroke_opacity=0)
            self._vertex_anchors.add(anchor)
        self.add(self._vertex_anchors)  # 锚点是 VGroup 的一部分，会随正方体旋转

        # 创建坐标轴（可选）
        if show_axes:
            self._create_axes()

        # 创建顶点标签（可选）
        if show_labels:
            self._create_vertex_labels()

    def _correct_face_normals(self, vertices: List[np.ndarray], faces: List[List[int]]) -> List[List[int]]:
        """
        法线自动校正（防御性编程）

        确保所有面的法线都指向外部（背离几何中心）。

        算法：
        1. 计算正方体的几何中心
        2. 对每个面：
           - 计算初步法线（使用右手定则）
           - 计算面中心到几何中心的向量
           - 如果法线指向内部（dot < 0），则翻转顶点顺序

        Parameters:
        -----------
        vertices : List[np.ndarray]
            顶点坐标列表
        faces : List[List[int]]
            面的顶点索引列表（可能顺序错误）

        Returns:
        --------
        List[List[int]]
            校正后的面的顶点索引列表（法线朝外）
        """
        # 1. 计算几何中心
        center = np.zeros(3)
        for v in vertices:
            center += v
        center /= len(vertices)

        corrected_faces = []

        # 2. 遍历每个面，校正法线方向
        for face in faces:
            # 获取面的前三个顶点
            v0 = np.array(vertices[face[0]], dtype=float)
            v1 = np.array(vertices[face[1]], dtype=float)
            v2 = np.array(vertices[face[2]], dtype=float)

            # 计算初步法线（右手定则）
            vec1 = v1 - v0
            vec2 = v2 - v1
            temp_normal = np.cross(vec1, vec2)

            # 归一化
            norm = np.linalg.norm(temp_normal)
            if norm < 1e-6:
                # 退化情况（三个点共线），保持原顺序
                corrected_faces.append(face)
                continue

            temp_normal = temp_normal / norm

            # 计算面中心
            face_center = np.zeros(3)
            for idx in face:
                face_center += vertices[idx]
            face_center /= len(face)

            # 计算面中心到几何中心的向量
            check_vec = face_center - center
            check_vec = check_vec / (np.linalg.norm(check_vec) + 1e-6)

            # 检查法线方向
            # 如果 dot(temp_normal, check_vec) < 0，说明法线指向内部
            if np.dot(temp_normal, check_vec) < 0:
                # 翻转顶点顺序
                corrected_face = face[::-1]
                print(f"[法线校正] 面顶点索引 {face} 法线向内，翻转为 {corrected_face}")
            else:
                corrected_face = face

            corrected_faces.append(corrected_face)

        return corrected_faces

    def _create_axes(self):
        """创建坐标轴"""
        axes = VGroup()
        L = self.axes_length

        # x 轴（红色，向右）
        x_axis = Line(
            start=ORIGIN,
            end=RIGHT * L,
            color=RED,
            stroke_width=3
        )
        x_label = MathTex("x", font_size=24, color=RED)
        x_label.next_to(x_axis.get_end(), RIGHT)

        # z 轴（绿色，向上）
        z_axis = Line(
            start=ORIGIN,
            end=UP * L,
            color=GREEN,
            stroke_width=3
        )
        z_label = MathTex("z", font_size=24, color=GREEN)
        z_label.next_to(z_axis.get_end(), UP)

        # y 轴（蓝色，向内）
        y_axis = Line(
            start=ORIGIN,
            end=OUT * L,
            color=BLUE,
            stroke_width=3
        )
        y_label = MathTex("y", font_size=24, color=BLUE)
        y_label.next_to(y_axis.get_end(), OUT + RIGHT)

        axes.add(x_axis, x_label, z_axis, z_label, y_axis, y_label)
        self.axes = axes
        self.add(axes)

    def _create_vertex_labels(self):
        """
        创建顶点标签

        注意：标签不添加到 self（VGroup）中，而是存储在 self.vertex_labels
        这样标签不会继承正方体的旋转变换
        """
        self.vertex_labels = []

        for i, (name, vertex) in enumerate(zip(self.vertex_names, self.vertices_local)):
            # 创建标签（使用字符串拼接）
            if "1" in name:
                base_name = name[0]
                label = MathTex(base_name + "_1", font_size=24, color=self.vertex_color)
            else:
                label = MathTex(name, font_size=24, color=self.vertex_color)

            # 设置初始位置（会被 updater 覆盖）
            label.move_to(vertex)

            # 保存标签对应的顶点索引
            label.vertex_idx = i

            self.vertex_labels.append(label)

    def get_global_vertices(self) -> List[np.ndarray]:
        """
        获取当前所有顶点的全局坐标（World Coordinates）

        通过隐藏的 Dot 锚点获取，确保返回的是变换后的绝对坐标

        Returns:
        --------
        List[np.ndarray]
            8 个顶点的全局坐标列表
        """
        global_vertices = []
        for anchor in self._vertex_anchors:
            global_vertices.append(anchor.get_center())
        return global_vertices

    def get_geometric_center(self) -> np.ndarray:
        """
        获取正方体的几何中心（不依赖 VGroup 的 bounding box）

        根据 8 个顶点的实际坐标计算，确保返回的是真正的几何中心

        Returns:
        --------
        np.ndarray
            几何中心坐标 [side_length/2, side_length/2, side_length/2]
        """
        vertices = self.get_global_vertices()
        center = np.zeros(3)
        for v in vertices:
            center += v
        return center / len(vertices)

    def get_vertex_coord(self, index: int) -> np.ndarray:
        """
        获取指定索引顶点的全局坐标

        Parameters:
        -----------
        index : int
            顶点索引（0-7）

        Returns:
        --------
        np.ndarray
            顶点的全局坐标
        """
        return self._vertex_anchors[index].get_center()

    def update_dashed_lines(self, camera_position: np.ndarray = None):
        """
        根据相机位置更新虚实线渲染

        不再处理标签更新，标签由场景级 updater 管理
        """
        # 只调用父类方法更新虚实线
        super().update_dashed_lines(camera_position)


class Cube(VGroup):
    """
    正方体组件的便捷包装类

    提供 simplified API，便于快速使用
    """

    def __init__(
        self,
        side_length: float = 2.0,
        origin_point: str = "A",
        show_axes: bool = True,
        show_labels: bool = True,
        **kwargs
    ):
        super().__init__(**kwargs)

        # 创建立方体几何体
        self.cube_geometry = CubeGeometry(
            side_length=side_length,
            origin_point=origin_point,
            show_axes=show_axes,
            show_labels=show_labels,
            **kwargs
        )
        self.add(self.cube_geometry)

    @property
    def vertex_labels(self):
        """代理属性：访问标签列表"""
        return self.cube_geometry.vertex_labels

    def get_global_vertices(self):
        """代理方法：获取全局顶点坐标"""
        return self.cube_geometry.get_global_vertices()

    def update_dashed_lines(self, camera_position=None):
        """代理方法：更新虚实线"""
        self.cube_geometry.update_dashed_lines(camera_position)

    def get_geometric_center(self):
        """代理方法：获取几何中心"""
        return self.cube_geometry.get_geometric_center()
