"""
立体几何基类 - Solid Geometry Base

提供多面体的通用功能，核心解决"虚实线处理"问题。

作者: Manim 数学组件库
日期: 2026-02-15
"""

from __future__ import annotations

import numpy as np
from manim import *
from typing import List, Tuple, Dict, Optional


class PolyhedronBase(VGroup):
    """
    多面体基类

    核心功能：
    1. 管理顶点和面的拓扑结构
    2. 根据相机位置自动判断棱边的可见性
    3. 动态更新虚实线渲染（教材标准）

    教材标准逻辑：
    - 如果一条棱连接的两个面都不可见，则该棱为虚线
    - 只要有一个面可见，则该棱为实线
    """

    def __init__(
        self,
        vertices: List[np.ndarray],
        faces: List[List[int]],
        edge_color: str = WHITE,
        vertex_color: str = YELLOW,
        dashed_color: str = GRAY,
        stroke_width: float = 4.0,
        **kwargs
    ):
        super().__init__(**kwargs)

        # 保存顶点坐标（局部坐标系）
        self.vertices_local = [np.array(v, dtype=float) for v in vertices]
        self.n_vertices = len(vertices)

        # 保存面索引（每个面由顶点索引组成，按逆时针顺序）
        self.faces = faces
        self.n_faces = len(faces)

        # 保存颜色配置
        self.edge_color = edge_color
        self.vertex_color = vertex_color
        self.dashed_color = dashed_color
        self.stroke_width = stroke_width

        # 构建棱边拓扑结构
        self._build_edge_topology()

        # 创建所有棱边（初始为实线）
        self._create_edges()

        # 创建顶点标记（可选）
        self.vertex_dots = VGroup()
        for i, vertex in enumerate(self.vertices_local):
            dot = Dot(point=vertex, radius=0.06, color=vertex_color)
            self.vertex_dots.add(dot)
        self.add(self.vertex_dots)

    def _build_edge_topology(self):
        """
        构建棱边拓扑结构

        对于每条棱，记录：
        - 棱的两个端点索引
        - 连接该棱的所有面索引
        """
        # 使用集合避免重复
        edge_set = set()
        edge_to_faces = {}

        for face_idx, face in enumerate(self.faces):
            n = len(face)
            for i in range(n):
                # 获取棱的两个端点（较小的索引在前，确保唯一性）
                v1, v2 = face[i], face[(i + 1) % n]
                if v1 > v2:
                    v1, v2 = v2, v1

                edge = (v1, v2)
                edge_set.add(edge)

                # 记录该棱连接的面
                if edge not in edge_to_faces:
                    edge_to_faces[edge] = []
                edge_to_faces[edge].append(face_idx)

        # 保存为列表（便于索引）
        self.edges = list(edge_set)
        self.edge_to_faces = edge_to_faces

    def _create_edges(self):
        """创建所有棱边的 Line 对象"""
        self.edge_lines = VGroup()
        self.edge_objects = {}  # edge -> Line 对象

        for edge in self.edges:
            v1_idx, v2_idx = edge
            start = self.vertices_local[v1_idx]
            end = self.vertices_local[v2_idx]

            # 创建实线
            line = Line(
                start=start,
                end=end,
                color=self.edge_color,
                stroke_width=self.stroke_width
            )
            self.edge_lines.add(line)
            self.edge_objects[edge] = line

        self.add(self.edge_lines)

    def _compute_face_normal(self, face: List[int]) -> np.ndarray:
        """
        计算面的法线向量（使用右手定则）

        假设面顶点按逆时针顺序排列
        """
        if len(face) < 3:
            return np.array([0, 0, 1])

        # 取前三个顶点计算法线
        v0 = self.vertices_local[face[0]]
        v1 = self.vertices_local[face[1]]
        v2 = self.vertices_local[face[2]]

        # 两个向量
        vec1 = v1 - v0
        vec2 = v2 - v0

        # 叉积得到法线
        normal = np.cross(vec1, vec2)

        # 归一化
        norm = np.linalg.norm(normal)
        if norm < 1e-6:
            return np.array([0, 0, 1])

        return normal / norm

    def _compute_face_center(self, face: List[int]) -> np.ndarray:
        """计算面的中心点"""
        center = np.zeros(3)
        for vertex_idx in face:
            center += self.vertices_local[vertex_idx]
        return center / len(face)

    def _is_face_visible(self, face_idx: int, camera_position: np.ndarray) -> bool:
        """
        判断面是否可见

        方法：计算面法线与视线向量的点积
        - 如果点积 < 0，说明面朝向相机，可见
        - 如果点积 >= 0，说明面背向相机，不可见
        """
        # 计算面中心的局部坐标
        face_center_local = self._compute_face_center(self.faces[face_idx])

        # 将面中心转换到世界坐标（考虑物体的变换）
        # 获取物体的变换矩阵
        face_center_world = self.get_family()[0].family_points_with_mobject()[0][0] \
            if hasattr(self, "points") and len(self.points) > 0 else face_center_local

        # 简化：直接使用物体的中心位置
        obj_center = self.get_center()
        face_center_world = obj_center + face_center_local

        # 计算视线向量（从相机指向面中心）
        view_vector = face_center_world - camera_position
        view_vector = view_vector / (np.linalg.norm(view_vector) + 1e-6)

        # 计算面法线（局部坐标）
        normal_local = self._compute_face_normal(self.faces[face_idx])

        # 将法线转换到世界坐标（考虑物体的旋转）
        # 简化处理：假设物体只进行了平移，没有复杂的旋转
        # 对于预旋转的物体，法线也需要相应旋转
        normal_world = normal_local

        # 计算点积
        dot_product = np.dot(view_vector, normal_world)

        # 点积 < 0 表示面朝向相机（可见）
        return dot_product < 0

    def update_dashed_lines(self, camera_position: np.ndarray = None):
        """
        根据相机位置更新虚实线渲染

        教材标准：
        - 如果一条棱连接的两个面都不可见，则该棱为虚线
        - 只要有一个面可见，则该棱为实线
        """
        if camera_position is None:
            # 使用当前相机的默认位置
            # 对于 ThreeDScene，相机位置可以通过 phi, theta 角度计算
            # 默认相机位置：使用球坐标 (distance=10, phi=0, theta=0)
            camera_position = self.get_camera_position()

        # 判断每个面的可见性
        face_visibility = []
        for face_idx in range(self.n_faces):
            visible = self._is_face_visible(face_idx, camera_position)
            face_visibility.append(visible)

        # 更新每条棱的渲染
        for edge in self.edges:
            line = self.edge_objects[edge]
            connected_faces = self.edge_to_faces[edge]

            # 检查连接的面是否都不可见
            all_faces_hidden = all(not face_visibility[f] for f in connected_faces)

            if all_faces_hidden:
                # 两个面都不可见 → 虚线
                line.set_style(
                    stroke_color=self.dashed_color,
                    stroke_opacity=0.5,
                    stroke_width=self.stroke_width * 0.7
                )
                # 注意：Manim 的 Line 不直接支持 dashed
                # 这里使用半透明灰色模拟虚线效果
            else:
                # 至少一个面可见 → 实线
                line.set_style(
                    stroke_color=self.edge_color,
                    stroke_opacity=1.0,
                    stroke_width=self.stroke_width
                )

    def get_camera_position(self) -> np.ndarray:
        """
        获取相机位置的近似估计

        注意：这是一个简化实现，适用于大多数场景
        对于精确的相机位置，建议从 Scene 中传入
        """
        # 默认相机位置：前方略上方
        # 球坐标：r=15, phi=30°, theta=-45°
        r = 15
        phi = 30 * DEGREES  # 与 yz 平面的夹角
        theta = -45 * DEGREES  # 在 xz 平面上的投影与 x 轴的夹角

        # 球坐标转直角坐标
        # x = r * sin(phi) * cos(theta)
        # y = r * cos(phi)
        # z = r * sin(phi) * sin(theta)

        x = r * np.sin(phi) * np.cos(theta)
        y = r * np.cos(phi)
        z = r * np.sin(phi) * np.sin(theta)

        return np.array([x, y, z])
