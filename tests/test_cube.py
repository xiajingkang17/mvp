"""
正方体组件测试演示 - Test Cube Geometry

展示 CubeGeometry 组件的使用方法和斜二测视角效果。

运行方法：
    manim -pql test_cube.py CubeDemo

作者: Manim 数学组件库
日期: 2026-02-15
"""

from manim import *
from manim.utils.space_ops import rotation_matrix
import sys
import os
import numpy as np

# 添加项目路径以导入自定义组件
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from components.solid_geometry.cube import CubeGeometry, Cube
from components.solid_geometry.oblique_cube import ObliqueCube
from components.solid_geometry.cylinder import CylinderOblique


class CubeDemo(ThreeDScene):
    """
    正方体演示场景

    展示功能：
    1. 标准正方体的绘制（新坐标系）
    2. 斜二测视角（phi=60°, theta=-45°）
    3. 自动虚实线渲染
    4. 标签始终朝向相机（解耦的 3D Billboard 效果）
    """

    def construct(self):
        # 设置相机角度
        self.set_camera_orientation(
            phi=60 * DEGREES,
            theta=-45 * DEGREES,
            gamma=0 * DEGREES
        )

        # 创建正方体
        cube = CubeGeometry(
            side_length=2.5,
            origin_point="A",
            show_axes=True,
            show_labels=True,
            edge_color=WHITE,
            vertex_color=YELLOW,
            stroke_width=4.0
        )

        # 添加正方体到场景
        self.add(cube)

        # 手动将标签添加到场景（标签与正方体解耦）
        if cube.show_labels:
            self.add(*cube.vertex_labels)

        # 添加场景说明文字
        title = Text("正方体演示", font_size=36)
        title.to_edge(UP)
        self.add_fixed_in_frame_mobjects(title)
        self.play(FadeIn(title))

        subtitle = Text("解耦的 3D Billboard 效果（修复自转 bug）", font_size=24)
        subtitle.next_to(title, DOWN)
        self.add_fixed_in_frame_mobjects(subtitle)
        self.play(FadeIn(subtitle))

        # 初始化虚实线
        cube.update_dashed_lines()

        self.wait(1)

        # 添加场景级 updater（管理标签）
        if cube.show_labels:
            self.add_updater(lambda dt: self._update_labels(cube, dt))

        # 相机旋转动画
        self.move_camera(theta=45 * DEGREES, phi=60 * DEGREES, run_time=4)
        self.wait(1)
        self.move_camera(theta=45 * DEGREES, phi=30 * DEGREES, run_time=3)
        self.wait(1)
        self.move_camera(theta=-45 * DEGREES, phi=60 * DEGREES, run_time=3)
        self.wait(1)
        self.move_camera(theta=-45 * DEGREES + 360 * DEGREES, phi=60 * DEGREES, run_time=8)
        self.wait(2)

    def _update_labels(self, cube: CubeGeometry, dt):
        """
        场景级 updater：更新所有标签的位置和朝向（Billboard 效果）
        修复了"自转不停"的 bug，使用绝对旋转矩阵
        """
        # 1. 获取相机位置
        phi = self.camera.phi
        theta = self.camera.theta
        r = 15
        camera_eye = np.array([
            r * np.sin(phi) * np.cos(theta),
            r * np.cos(phi),
            r * np.sin(phi) * np.sin(theta)
        ])

        # 2. 获取正方体当前的全局顶点坐标
        current_vertices = cube.get_global_vertices()
        cube_center = cube.get_center()

        for label, v_pos in zip(cube.vertex_labels, current_vertices):
            # --- 位置同步 ---
            target_pos = v_pos.copy()
            out_vector = v_pos - cube_center
            out_norm = np.linalg.norm(out_vector)
            if out_norm > 1e-6:
                target_pos += (out_vector / out_norm) * 0.4
            label.move_to(target_pos)

            # --- 朝向同步 (Billboard) ---
            # 关键修复：直接操作点的绝对旋转
            label_pos = label.get_center()
            to_camera = camera_eye - label_pos
            to_camera = to_camera / np.linalg.norm(to_camera)

            # 计算绕 UP 轴的旋转（水平方向）
            xz_projection = np.array([to_camera[0], 0, to_camera[2]])
            if np.linalg.norm(xz_projection) > 1e-6:
                xz_projection = xz_projection / np.linalg.norm(xz_projection)
                angle_xz = np.arctan2(xz_projection[0], -xz_projection[2])
                rot_matrix = rotation_matrix(angle_xz, axis=UP)
                label.points = np.dot(label.points, rot_matrix.T)

            # 计算绕 RIGHT 轴的旋转（仰角方向）
            horizontal_dist = np.sqrt(to_camera[0]**2 + to_camera[2]**2)
            if horizontal_dist > 1e-6:
                angle_elevation = np.arctan2(to_camera[1], horizontal_dist)
                rot_matrix = rotation_matrix(angle_elevation, axis=RIGHT)
                label.points = np.dot(label.points, rot_matrix.T)


class CubeSimpleDemo(ThreeDScene):
    """简化版正方体演示"""

    def construct(self):
        # 设置斜二测视角
        self.set_camera_orientation(phi=60 * DEGREES, theta=-45 * DEGREES)

        # 创建正方体
        cube = Cube(
            side_length=2.0,
            origin_point="A",
            show_axes=True,
            show_labels=True
        )

        # 添加到场景
        self.add(cube)

        # 手动将标签添加到场景
        if cube.show_labels:
            self.add(*cube.vertex_labels)

        # 初始化虚实线
        cube.update_dashed_lines()

        # 添加 updater
        if cube.show_labels:
            self.add_updater(lambda dt: self._update_labels(cube, dt))

        # 相机旋转
        self.move_camera(theta=45 * DEGREES, phi=60 * DEGREES, run_time=4)
        self.move_camera(theta=-45 * DEGREES, phi=60 * DEGREES, run_time=4)

        self.wait()

    def _update_labels(self, cube: CubeGeometry, dt):
        """更新标签的位置和朝向（修复自转 bug）"""
        phi = self.camera.phi
        theta = self.camera.theta
        r = 15
        camera_eye = np.array([
            r * np.sin(phi) * np.cos(theta),
            r * np.cos(phi),
            r * np.sin(phi) * np.sin(theta)
        ])

        current_vertices = cube.get_global_vertices()
        cube_center = cube.get_center()

        for label, v_pos in zip(cube.vertex_labels, current_vertices):
            target_pos = v_pos.copy()
            out_vector = v_pos - cube_center
            out_norm = np.linalg.norm(out_vector)
            if out_norm > 1e-6:
                target_pos += (out_vector / out_norm) * 0.4
            label.move_to(target_pos)

            label_pos = label.get_center()
            to_camera = camera_eye - label_pos
            to_camera = to_camera / np.linalg.norm(to_camera)

            xz_projection = np.array([to_camera[0], 0, to_camera[2]])
            if np.linalg.norm(xz_projection) > 1e-6:
                xz_projection = xz_projection / np.linalg.norm(xz_projection)
                angle_xz = np.arctan2(xz_projection[0], -xz_projection[2])
                rot_matrix = rotation_matrix(angle_xz, axis=UP)
                label.points = np.dot(label.points, rot_matrix.T)

            horizontal_dist = np.sqrt(to_camera[0]**2 + to_camera[2]**2)
            if horizontal_dist > 1e-6:
                angle_elevation = np.arctan2(to_camera[1], horizontal_dist)
                rot_matrix = rotation_matrix(angle_elevation, axis=RIGHT)
                label.points = np.dot(label.points, rot_matrix.T)


class CubeRotateDemo(ThreeDScene):
    """
    正方体自身旋转演示

    重点展示标签跟随顶点移动但始终朝向相机的效果
    """

    def construct(self):
        # 设置视角
        self.set_camera_orientation(phi=60 * DEGREES, theta=-45 * DEGREES)

        # 创建正方体
        cube = CubeGeometry(
            side_length=2.0,
            origin_point="A",
            show_axes=True,
            show_labels=True
        )

        # 添加到场景
        self.add(cube)

        # 手动将标签添加到场景
        if cube.show_labels:
            self.add(*cube.vertex_labels)

        # 初始化
        cube.update_dashed_lines()

        # 添加说明
        title = Text("正方体旋转演示（修复自转 bug）", font_size=36)
        title.to_edge(UP)
        self.add_fixed_in_frame_mobjects(title)

        note = Text("标签跟随顶点移动但始终朝向相机", font_size=20)
        note.next_to(title, DOWN)
        self.add_fixed_in_frame_mobjects(note)

        self.wait(1)

        # 添加 updater
        if cube.show_labels:
            self.add_updater(lambda dt: self._update_labels(cube, dt))

        # 让正方体绕 UP 轴旋转
        self.play(Rotate(cube, angle=2 * PI, axis=UP), run_time=8)
        self.wait(1)

        # 让正方体绕 RIGHT 轴旋转
        self.play(Rotate(cube, angle=2 * PI, axis=RIGHT), run_time=8)
        self.wait(1)

        # 让正方体绕 OUT 轴旋转
        self.play(Rotate(cube, angle=2 * PI, axis=OUT), run_time=8)

        self.wait(2)

    def _update_labels(self, cube: CubeGeometry, dt):
        """更新标签的位置和朝向（修复自转 bug）"""
        phi = self.camera.phi
        theta = self.camera.theta
        r = 15
        camera_eye = np.array([
            r * np.sin(phi) * np.cos(theta),
            r * np.cos(phi),
            r * np.sin(phi) * np.sin(theta)
        ])

        current_vertices = cube.get_global_vertices()
        cube_center = cube.get_center()

        for label, v_pos in zip(cube.vertex_labels, current_vertices):
            target_pos = v_pos.copy()
            out_vector = v_pos - cube_center
            out_norm = np.linalg.norm(out_vector)
            if out_norm > 1e-6:
                target_pos += (out_vector / out_norm) * 0.4
            label.move_to(target_pos)

            label_pos = label.get_center()
            to_camera = camera_eye - label_pos
            to_camera = to_camera / np.linalg.norm(to_camera)

            xz_projection = np.array([to_camera[0], 0, to_camera[2]])
            if np.linalg.norm(xz_projection) > 1e-6:
                xz_projection = xz_projection / np.linalg.norm(xz_projection)
                angle_xz = np.arctan2(xz_projection[0], -xz_projection[2])
                rot_matrix = rotation_matrix(angle_xz, axis=UP)
                label.points = np.dot(label.points, rot_matrix.T)

            horizontal_dist = np.sqrt(to_camera[0]**2 + to_camera[2]**2)
            if horizontal_dist > 1e-6:
                angle_elevation = np.arctan2(to_camera[1], horizontal_dist)
                rot_matrix = rotation_matrix(angle_elevation, axis=RIGHT)
                label.points = np.dot(label.points, rot_matrix.T)


class CubeBillboardDemo(ThreeDScene):
    """3D Billboard 效果专门演示（解耦版）"""

    def construct(self):
        # 设置初始视角
        self.set_camera_orientation(phi=60 * DEGREES, theta=-45 * DEGREES)

        # 创建正方体
        cube = CubeGeometry(
            side_length=2.5,
            origin_point="A",
            show_axes=True,
            show_labels=True
        )

        # 添加到场景
        self.add(cube)

        # 手动将标签添加到场景
        if cube.show_labels:
            self.add(*cube.vertex_labels)

        # 初始化
        cube.update_dashed_lines()

        # 添加说明
        title = Text("解耦的 3D Billboard 效果（修复版）", font_size=36)
        title.to_edge(UP)
        self.add_fixed_in_frame_mobjects(title)
        self.play(FadeIn(title))

        note = Text("标签跟随顶点，不继承正方体旋转", font_size=20)
        note.next_to(title, DOWN)
        self.add_fixed_in_frame_mobjects(note)
        self.play(FadeIn(note))

        self.wait(1)

        # 添加 updater
        if cube.show_labels:
            self.add_updater(lambda dt: self._update_labels(cube, dt))

        # 全方位旋转展示
        angles = [
            (0 * DEGREES, 60 * DEGREES),
            (90 * DEGREES, 60 * DEGREES),
            (180 * DEGREES, 60 * DEGREES),
            (270 * DEGREES, 60 * DEGREES),
            (-45 * DEGREES, 60 * DEGREES),
        ]

        for theta, phi in angles:
            self.move_camera(theta=theta, phi=phi, run_time=2)
            self.wait(0.5)

        # 上下旋转
        self.move_camera(theta=-45 * DEGREES, phi=30 * DEGREES, run_time=2)
        self.wait(0.5)

        self.move_camera(theta=-45 * DEGREES, phi=90 * DEGREES, run_time=2)
        self.wait(0.5)

        # 恢复标准视角
        self.move_camera(theta=-45 * DEGREES, phi=60 * DEGREES, run_time=2)

        self.wait(2)

    def _update_labels(self, cube: CubeGeometry, dt):
        """更新标签的位置和朝向（修复自转 bug）"""
        phi = self.camera.phi
        theta = self.camera.theta
        r = 15
        camera_eye = np.array([
            r * np.sin(phi) * np.cos(theta),
            r * np.cos(phi),
            r * np.sin(phi) * np.sin(theta)
        ])

        current_vertices = cube.get_global_vertices()
        cube_center = cube.get_center()

        for label, v_pos in zip(cube.vertex_labels, current_vertices):
            target_pos = v_pos.copy()
            out_vector = v_pos - cube_center
            out_norm = np.linalg.norm(out_vector)
            if out_norm > 1e-6:
                target_pos += (out_vector / out_norm) * 0.4
            label.move_to(target_pos)

            label_pos = label.get_center()
            to_camera = camera_eye - label_pos
            to_camera = to_camera / np.linalg.norm(to_camera)

            xz_projection = np.array([to_camera[0], 0, to_camera[2]])
            if np.linalg.norm(xz_projection) > 1e-6:
                xz_projection = xz_projection / np.linalg.norm(xz_projection)
                angle_xz = np.arctan2(xz_projection[0], -xz_projection[2])
                rot_matrix = rotation_matrix(angle_xz, axis=UP)
                label.points = np.dot(label.points, rot_matrix.T)

            horizontal_dist = np.sqrt(to_camera[0]**2 + to_camera[2]**2)
            if horizontal_dist > 1e-6:
                angle_elevation = np.arctan2(to_camera[1], horizontal_dist)
                rot_matrix = rotation_matrix(angle_elevation, axis=RIGHT)
                label.points = np.dot(label.points, rot_matrix.T)


class CubeCoordinateDemo(ThreeDScene):
    """坐标系演示"""

    def construct(self):
        # 设置视角
        self.set_camera_orientation(phi=60 * DEGREES, theta=-45 * DEGREES)

        # 创建正方体
        cube = CubeGeometry(
            side_length=2.0,
            origin_point="A",
            show_axes=True,
            show_labels=True,
            edge_color=WHITE,
            vertex_color=YELLOW
        )

        # 添加到场景
        self.add(cube)

        # 手动将标签添加到场景
        if cube.show_labels:
            self.add(*cube.vertex_labels)

        cube.update_dashed_lines()

        # 添加坐标系说明
        info_lines = VGroup()
        infos = [
            "新坐标系定义：",
            "A = (0, 0, 0)  ← 原点",
            "B = (L, 0, 0)  ← x 轴正方向",
            "D = (0, L, 0)  ← y 轴正方向",
            "A1 = (0, 0, L) ← z 轴正方向",
        ]

        for i, info in enumerate(infos):
            text = Text(info, font_size=20, color=WHITE if i > 0 else YELLOW)
            text.to_edge(UP)
            text.shift(DOWN * i * 0.4)
            info_lines.add(text)

        self.add_fixed_in_frame_mobjects(info_lines)
        self.play(FadeIn(info_lines))

        self.wait(2)

        # 添加 updater
        if cube.show_labels:
            self.add_updater(lambda dt: self._update_labels(cube, dt))

        # 缓慢旋转
        self.move_camera(theta=315 * DEGREES, phi=60 * DEGREES, run_time=10)

        self.wait(2)

    def _update_labels(self, cube: CubeGeometry, dt):
        """更新标签的位置和朝向（修复自转 bug）"""
        phi = self.camera.phi
        theta = self.camera.theta
        r = 15
        camera_eye = np.array([
            r * np.sin(phi) * np.cos(theta),
            r * np.cos(phi),
            r * np.sin(phi) * np.sin(theta)
        ])

        current_vertices = cube.get_global_vertices()
        cube_center = cube.get_center()

        for label, v_pos in zip(cube.vertex_labels, current_vertices):
            target_pos = v_pos.copy()
            out_vector = v_pos - cube_center
            out_norm = np.linalg.norm(out_vector)
            if out_norm > 1e-6:
                target_pos += (out_vector / out_norm) * 0.4
            label.move_to(target_pos)

            label_pos = label.get_center()
            to_camera = camera_eye - label_pos
            to_camera = to_camera / np.linalg.norm(to_camera)

            xz_projection = np.array([to_camera[0], 0, to_camera[2]])
            if np.linalg.norm(xz_projection) > 1e-6:
                xz_projection = xz_projection / np.linalg.norm(xz_projection)
                angle_xz = np.arctan2(xz_projection[0], -xz_projection[2])
                rot_matrix = rotation_matrix(angle_xz, axis=UP)
                label.points = np.dot(label.points, rot_matrix.T)

            horizontal_dist = np.sqrt(to_camera[0]**2 + to_camera[2]**2)
            if horizontal_dist > 1e-6:
                angle_elevation = np.arctan2(to_camera[1], horizontal_dist)
                rot_matrix = rotation_matrix(angle_elevation, axis=RIGHT)
                label.points = np.dot(label.points, rot_matrix.T)


class CubeMultipleOrigins(ThreeDScene):
    """不同原点选择的对比演示"""

    def construct(self):
        # 设置视角
        self.set_camera_orientation(phi=60 * DEGREES, theta=-45 * DEGREES)

        # 创建三个不同原点的正方体
        cube_a = CubeGeometry(
            side_length=1.5,
            origin_point="A",
            show_axes=True,
            show_labels=True,
            edge_color=WHITE
        )
        cube_a.shift(LEFT * 4)

        cube_b = CubeGeometry(
            side_length=1.5,
            origin_point="B",
            show_axes=True,
            show_labels=True,
            edge_color=BLUE
        )

        cube_c = CubeGeometry(
            side_length=1.5,
            origin_point="C",
            show_axes=True,
            show_labels=True,
            edge_color=GREEN
        )
        cube_c.shift(RIGHT * 4)

        # 添加到场景
        self.add(cube_a, cube_b, cube_c)

        # 手动将标签添加到场景
        if cube_a.show_labels:
            self.add(*cube_a.vertex_labels)
        if cube_b.show_labels:
            self.add(*cube_b.vertex_labels)
        if cube_c.show_labels:
            self.add(*cube_c.vertex_labels)

        # 初始化
        cube_a.update_dashed_lines()
        cube_b.update_dashed_lines()
        cube_c.update_dashed_lines()

        # 添加标签
        label_a = Text("原点: A", font_size=20, color=WHITE)
        label_a.next_to(cube_a, DOWN)
        label_b = Text("原点: B", font_size=20, color=BLUE)
        label_b.next_to(cube_b, DOWN)
        label_c = Text("原点: C", font_size=20, color=GREEN)
        label_c.next_to(cube_c, DOWN)

        self.add_fixed_in_frame_mobjects(label_a, label_b, label_c)

        # 添加说明
        title = Text("不同原点选择对比", font_size=36)
        title.to_edge(UP)
        self.add_fixed_in_frame_mobjects(title)

        self.wait(2)

        # 添加 updater
        self.add_updater(lambda dt: self._update_all_cubes(cube_a, cube_b, cube_c, dt))

        # 旋转
        self.move_camera(theta=45 * DEGREES, phi=60 * DEGREES, run_time=5)
        self.wait(1)
        self.move_camera(theta=-45 * DEGREES, phi=60 * DEGREES, run_time=5)

        self.wait(2)

    def _update_all_cubes(self, cube_a, cube_b, cube_c, dt):
        """更新所有正方体的标签（修复自转 bug）"""
        phi = self.camera.phi
        theta = self.camera.theta
        r = 15
        camera_eye = np.array([
            r * np.sin(phi) * np.cos(theta),
            r * np.cos(phi),
            r * np.sin(phi) * np.sin(theta)
        ])

        for cube in [cube_a, cube_b, cube_c]:
            if not cube.show_labels:
                continue

            current_vertices = cube.get_global_vertices()
            cube_center = cube.get_center()

            for label, v_pos in zip(cube.vertex_labels, current_vertices):
                target_pos = v_pos.copy()
                out_vector = v_pos - cube_center
                out_norm = np.linalg.norm(out_vector)
                if out_norm > 1e-6:
                    target_pos += (out_vector / out_norm) * 0.4
                label.move_to(target_pos)

                label_pos = label.get_center()
                to_camera = camera_eye - label_pos
                to_camera = to_camera / np.linalg.norm(to_camera)

                xz_projection = np.array([to_camera[0], 0, to_camera[2]])
                if np.linalg.norm(xz_projection) > 1e-6:
                    xz_projection = xz_projection / np.linalg.norm(xz_projection)
                    angle_xz = np.arctan2(xz_projection[0], -xz_projection[2])
                    rot_matrix = rotation_matrix(angle_xz, axis=UP)
                    label.points = np.dot(label.points, rot_matrix.T)

                horizontal_dist = np.sqrt(to_camera[0]**2 + to_camera[2]**2)
                if horizontal_dist > 1e-6:
                    angle_elevation = np.arctan2(to_camera[1], horizontal_dist)
                    rot_matrix = rotation_matrix(angle_elevation, axis=RIGHT)
                    label.points = np.dot(label.points, rot_matrix.T)


class CubeStaticReference(ThreeDScene):
    """
    静态正方体参考场景

    完美的、静态的正方体场景，严格参考教材图片布局。
    标签使用简化的朝向设置，无需复杂的 updater。
    """

    def construct(self):
        # 设置固定的高角度视角
        self.set_camera_orientation(
            phi=70 * DEGREES,
            theta=-45 * DEGREES
        )

        # 添加标准坐标轴
        axes = ThreeDAxes(
            x_range=[0, 5, 1],
            y_range=[0, 5, 1],
            z_range=[0, 5, 1],
            x_length=5,
            y_length=5,
            z_length=5
        )
        self.add(axes)

        # 创建正方体（顶点 A 在原点，边长 3）
        cube = CubeGeometry(
            side_length=3.0,
            origin_point="A",  # 确保 A 在 (0,0,0)
            show_axes=False,  # 已经单独添加了坐标轴
            show_labels=True,
            edge_color=WHITE,
            vertex_color=YELLOW,
            stroke_width=4.0
        )

        # 添加正方体到场景
        self.add(cube)

        # 手动将标签添加到场景
        if cube.show_labels:
            self.add(*cube.vertex_labels)

        # 初始化虚实线渲染（传入相机位置）
        # 计算相机位置
        phi = 70 * DEGREES  # 与 set_camera_orientation 一致
        theta = -45 * DEGREES
        r = 15  # 默认相机距离
        camera_eye = np.array([
            r * np.sin(phi) * np.cos(theta),
            r * np.cos(phi),
            r * np.sin(phi) * np.sin(theta)
        ])
        cube.update_dashed_lines(camera_eye)

        # 为每个标签设置朝向（静态，一次性设置）
        if cube.show_labels:
            for label in cube.vertex_labels:
                # 尝试使用 look_at 方法（如果可用）
                try:
                    label.look_at(camera_eye)
                    # 修正镜像问题，让文字正过来
                    label.rotate(PI, axis=UP)
                except AttributeError:
                    # 如果 look_at 不可用，使用手动旋转
                    # 获取标签当前位置
                    label_pos = label.get_center()
                    # 计算从标签到相机的向量
                    to_camera = camera_eye - label_pos
                    to_camera = to_camera / np.linalg.norm(to_camera)

                    # 计算绕 UP 轴的旋转（水平方向）
                    xz_projection = np.array([to_camera[0], 0, to_camera[2]])
                    if np.linalg.norm(xz_projection) > 1e-6:
                        xz_projection = xz_projection / np.linalg.norm(xz_projection)
                        angle_xz = np.arctan2(xz_projection[0], -xz_projection[2])
                        rot_matrix = rotation_matrix(angle_xz, axis=UP)
                        label.points = np.dot(label.points, rot_matrix.T)

                    # 计算绕 RIGHT 轴的旋转（仰角方向）
                    horizontal_dist = np.sqrt(to_camera[0]**2 + to_camera[2]**2)
                    if horizontal_dist > 1e-6:
                        angle_elevation = np.arctan2(to_camera[1], horizontal_dist)
                        rot_matrix = rotation_matrix(angle_elevation, axis=RIGHT)
                        label.points = np.dot(label.points, rot_matrix.T)

                    # 修正镜像
                    label.rotate(PI, axis=UP)

        # 添加标题（2D，固定在屏幕上）
        title = Text("静态正方体参考图", font_size=36)
        title.to_edge(UP)
        self.add_fixed_in_frame_mobjects(title)

        # 静态场景，无动画，无需 updater
        # 渲染完成后自动停止


class CubeTextbookStatic(ThreeDScene):
    """
    完美的静态正方体场景（教材风格）

    核心修复：
    1. 使用 focal_point 确保正方体居中
    2. 手动设置标签位置和朝向
    3. 正确的虚实线渲染
    4. 适当的坐标轴范围
    """

    def construct(self):
        # ========== 正方体参数 ==========
        side_length = 3.0

        # ========== 创建正方体 ==========
        cube = CubeGeometry(
            side_length=side_length,
            origin_point="A",  # A 点在原点 (0,0,0)
            show_axes=False,  # 我们将手动创建坐标轴
            show_labels=True,
            edge_color=WHITE,
            vertex_color=YELLOW,
            stroke_width=4.0
        )

        # ========== 创建坐标轴 ==========
        # 范围略大于正方体边长，避免被切断
        axis_length = side_length * 1.5
        axes = ThreeDAxes(
            x_range=[0, axis_length, 1],
            y_range=[0, axis_length, 1],
            z_range=[0, axis_length, 1],
            x_length=axis_length,
            y_length=axis_length,
            z_length=axis_length
        )

        # ========== 设置相机（关键：使用 focal_point） ==========
        # 计算正方体几何中心
        cube_center = cube.get_center()

        # 设置相机角度，焦点对准正方体中心
        self.set_camera_orientation(
            phi=70 * DEGREES,
            theta=-45 * DEGREES,
            focal_point=cube_center,  # 关键：确保正方体居中
            zoom=0.8  # 适当缩放，确保坐标轴不被切断
        )

        # ========== 计算相机位置 ==========
        phi = 70 * DEGREES
        theta = -45 * DEGREES
        r = 15  # 默认相机距离
        camera_eye = np.array([
            r * np.sin(phi) * np.cos(theta),
            r * np.cos(phi),
            r * np.sin(phi) * np.sin(theta)
        ])

        # ========== 添加到场景 ==========
        self.add(axes)
        self.add(cube)

        # ========== 手动将标签添加到场景 ==========
        if cube.show_labels:
            self.add(*cube.vertex_labels)

        # ========== 初始化虚实线渲染 ==========
        cube.update_dashed_lines(camera_eye)

        # ========== 手动设置标签位置和朝向（静态，一次性） ==========
        if cube.show_labels:
            # 获取所有顶点的全局坐标
            vertices = cube.get_global_vertices()
            cube_center = cube.get_center()

            for i, label in enumerate(cube.vertex_labels):
                # 1. 位置：贴合顶点
                vertex_pos = vertices[i]

                # 2. 向外偏移，避免压住线
                # 计算从正方体中心到顶点的向量
                out_vector = vertex_pos - cube_center
                out_norm = np.linalg.norm(out_vector)
                if out_norm > 1e-6:
                    offset_dir = out_vector / out_norm
                    # 向外偏移 0.5 单位
                    vertex_pos = vertex_pos + offset_dir * 0.5

                label.move_to(vertex_pos)

                # 3. 朝向：强制面向相机
                try:
                    # 尝试使用 look_at 方法
                    label.look_at(camera_eye)
                except AttributeError:
                    # 如果 look_at 不可用，使用手动旋转
                    label_pos = label.get_center()
                    to_camera = camera_eye - label_pos
                    to_camera = to_camera / np.linalg.norm(to_camera)

                    # 绕 UP 轴旋转（水平方向）
                    xz_projection = np.array([to_camera[0], 0, to_camera[2]])
                    if np.linalg.norm(xz_projection) > 1e-6:
                        xz_projection = xz_projection / np.linalg.norm(xz_projection)
                        angle_xz = np.arctan2(xz_projection[0], -xz_projection[2])
                        rot_matrix = rotation_matrix(angle_xz, axis=UP)
                        label.points = np.dot(label.points, rot_matrix.T)

                    # 绕 RIGHT 轴旋转（仰角方向）
                    horizontal_dist = np.sqrt(to_camera[0]**2 + to_camera[2]**2)
                    if horizontal_dist > 1e-6:
                        angle_elevation = np.arctan2(to_camera[1], horizontal_dist)
                        rot_matrix = rotation_matrix(angle_elevation, axis=RIGHT)
                        label.points = np.dot(label.points, rot_matrix.T)

                # 4. 修正镜像
                label.rotate(PI, axis=UP)

                # 5. 设置高亮颜色（防止与背景混淆）
                label.set_color(RED)

                # 6. 调整大小
                label.scale(0.8)

        # ========== 添加标题（可选） ==========
        # 如果需要标题，取消下面的注释
        # title = Text("正方体（教材风格）", font_size=36)
        # title.to_edge(UP)
        # self.add_fixed_in_frame_mobjects(title)

        # ========== 静态场景，无动画 ==========


class CubeFixedPositionDemo(ThreeDScene):
    """
    修复位置的正方体演示

    核心修复：
    1. 使用几何中心作为 focal_point（而不是 get_center()）
    2. 确保 A 点与坐标轴原点重合
    3. 标准教材视角（phi=75°, theta=-45°）
    """

    def construct(self):
        # ========== 正方体参数 ==========
        side_length = 3.0

        # ========== 创建正方体 ==========
        cube = CubeGeometry(
            side_length=side_length,
            origin_point="A",  # A 点必须在 (0,0,0)
            show_axes=False,  # 手动创建坐标轴
            show_labels=True,
            edge_color=WHITE,
            vertex_color=YELLOW,
            stroke_width=4.0
        )

        # ========== 调试输出：验证 A 点位置 ==========
        vertices = cube.get_global_vertices()
        print(f"\n========== 调试信息 ==========")
        print(f"A 点坐标 (vertices[0]): {vertices[0]}")
        print(f"预期: [0. 0. 0.]")
        print(f"几何中心: {cube.get_geometric_center()}")
        print(f"预期几何中心: [{side_length/2}, {side_length/2}, {side_length/2}]")
        print(f"VGroup 中心: {cube.get_center()}")
        print(f"============================\n")

        # ========== 创建坐标轴 ==========
        axis_length = side_length * 1.5
        axes = ThreeDAxes(
            x_range=[0, axis_length, 1],
            y_range=[0, axis_length, 1],
            z_range=[0, axis_length, 1],
            x_length=axis_length,
            y_length=axis_length,
            z_length=axis_length
        )

        # ========== 计算几何中心（关键修复）==========
        # 使用几何中心，而不是 VGroup 的 bounding box 中心
        geometric_center = cube.get_geometric_center()
        print(f"使用几何中心作为 focal_point: {geometric_center}")

        # ========== 设置相机（标准教材视角）==========
        self.set_camera_orientation(
            phi=75 * DEGREES,   # 俯视角度
            theta=-45 * DEGREES,  # 45度角侧视（标准教材视角）
            focal_point=geometric_center,  # 关键：使用几何中心
            zoom=0.8
        )

        # ========== 计算相机位置 ==========
        phi = 75 * DEGREES
        theta = -45 * DEGREES
        r = 15
        camera_eye = np.array([
            r * np.sin(phi) * np.cos(theta),
            r * np.cos(phi),
            r * np.sin(phi) * np.sin(theta)
        ])

        # ========== 添加到场景 ==========
        self.add(axes)
        self.add(cube)

        # ========== 手动将标签添加到场景 ==========
        if cube.show_labels:
            self.add(*cube.vertex_labels)

        # ========== 初始化虚实线渲染 ==========
        cube.update_dashed_lines(camera_eye)

        # ========== 手动设置标签位置和朝向 ==========
        if cube.show_labels:
            vertices = cube.get_global_vertices()
            cube_center = cube.get_geometric_center()

            for i, label in enumerate(cube.vertex_labels):
                # 1. 位置：贴合顶点
                vertex_pos = vertices[i]

                # 2. 向外偏移
                out_vector = vertex_pos - cube_center
                out_norm = np.linalg.norm(out_vector)
                if out_norm > 1e-6:
                    offset_dir = out_vector / out_norm
                    vertex_pos = vertex_pos + offset_dir * 0.5

                label.move_to(vertex_pos)

                # 3. 朝向：强制面向相机
                try:
                    label.look_at(camera_eye)
                except AttributeError:
                    # 手动旋转
                    label_pos = label.get_center()
                    to_camera = camera_eye - label_pos
                    to_camera = to_camera / np.linalg.norm(to_camera)

                    # 绕 UP 轴旋转
                    xz_projection = np.array([to_camera[0], 0, to_camera[2]])
                    if np.linalg.norm(xz_projection) > 1e-6:
                        xz_projection = xz_projection / np.linalg.norm(xz_projection)
                        angle_xz = np.arctan2(xz_projection[0], -xz_projection[2])
                        rot_matrix = rotation_matrix(angle_xz, axis=UP)
                        label.points = np.dot(label.points, rot_matrix.T)

                    # 绕 RIGHT 轴旋转
                    horizontal_dist = np.sqrt(to_camera[0]**2 + to_camera[2]**2)
                    if horizontal_dist > 1e-6:
                        angle_elevation = np.arctan2(to_camera[1], horizontal_dist)
                        rot_matrix = rotation_matrix(angle_elevation, axis=RIGHT)
                        label.points = np.dot(label.points, rot_matrix.T)

                # 4. 修正镜像
                label.rotate(PI, axis=UP)

                # 5. 设置颜色和大小
                label.set_color(RED)
                label.scale(0.8)

        # ========== 静态场景，无动画 ==========


class CubeFinalFix(ThreeDScene):
    """
    最终修复版本（防御性编程）

    核心特性：
    1. 法线自动校正（在 cube.py 中实现）
    2. 调试小球验证 A 点位置
    3. 标准教材视角（phi=60°, theta=-45°）
    4. 完美的虚实线渲染
    """

    def construct(self):
        # ========== 正方体参数 ==========
        side_length = 3.0

        # ========== 创建正方体 ==========
        print("\n========== 创建正方体 ==========")
        cube = CubeGeometry(
            side_length=side_length,
            origin_point="A",  # A 点必须在 (0,0,0)
            show_axes=False,  # 手动创建坐标轴
            show_labels=True,
            edge_color=WHITE,
            vertex_color=YELLOW,
            stroke_width=4.0
        )
        print("正方体创建完成\n")

        # ========== 创建坐标轴 ==========
        axis_length = side_length * 1.5
        axes = ThreeDAxes(
            x_range=[0, axis_length, 1],
            y_range=[0, axis_length, 1],
            z_range=[0, axis_length, 1],
            x_length=axis_length,
            y_length=axis_length,
            z_length=axis_length
        )

        # ========== 调试小球（关键）==========
        # 创建一个黄色小球在原点，用于验证 A 点位置
        origin_sphere = Dot3D(point=ORIGIN, color=YELLOW, radius=0.15)
        print(f"调试小球位置: {origin_sphere.get_center()}")
        print(f"预期位置: [0. 0. 0.]")

        # 验证正方体 A 点位置
        vertices = cube.get_global_vertices()
        print(f"正方体 A 点位置: {vertices[0]}")
        print(f"匹配检查: {np.allclose(vertices[0], ORIGIN)}\n")

        # ========== 计算几何中心 ==========
        geometric_center = cube.get_geometric_center()
        print(f"几何中心: {geometric_center}")
        print(f"预期: [{side_length/2}, {side_length/2}, {side_length/2}]\n")

        # ========== 设置相机（标准教材视角）==========
        self.set_camera_orientation(
            phi=60 * DEGREES,      # 标准的 60 度俯角
            theta=-45 * DEGREES,   # 标准的斜二测角度
            focal_point=geometric_center,  # 使用几何中心
            zoom=0.6  # 稍微拉远一点
        )

        # ========== 计算相机位置 ==========
        phi = 60 * DEGREES
        theta = -45 * DEGREES
        r = 15
        camera_eye = np.array([
            r * np.sin(phi) * np.cos(theta),
            r * np.cos(phi),
            r * np.sin(phi) * np.sin(theta)
        ])
        print(f"相机位置: {camera_eye}\n")

        # ========== 添加到场景 ==========
        self.add(axes)
        self.add(cube)
        self.add(origin_sphere)  # 添加调试小球

        # ========== 手动将标签添加到场景 ==========
        if cube.show_labels:
            self.add(*cube.vertex_labels)

        # ========== 初始化虚实线渲染 ==========
        cube.update_dashed_lines(camera_eye)
        print("虚实线渲染完成\n")

        # ========== 手动设置标签位置和朝向 ==========
        if cube.show_labels:
            vertices = cube.get_global_vertices()
            cube_center = cube.get_geometric_center()

            for i, label in enumerate(cube.vertex_labels):
                # 1. 位置：贴合顶点
                vertex_pos = vertices[i]

                # 2. 向外偏移
                out_vector = vertex_pos - cube_center
                out_norm = np.linalg.norm(out_vector)
                if out_norm > 1e-6:
                    offset_dir = out_vector / out_norm
                    vertex_pos = vertex_pos + offset_dir * 0.5

                label.move_to(vertex_pos)

                # 3. 朝向：强制面向相机
                try:
                    label.look_at(camera_eye)
                except AttributeError:
                    # 手动旋转
                    label_pos = label.get_center()
                    to_camera = camera_eye - label_pos
                    to_camera = to_camera / np.linalg.norm(to_camera)

                    # 绕 UP 轴旋转
                    xz_projection = np.array([to_camera[0], 0, to_camera[2]])
                    if np.linalg.norm(xz_projection) > 1e-6:
                        xz_projection = xz_projection / np.linalg.norm(xz_projection)
                        angle_xz = np.arctan2(xz_projection[0], -xz_projection[2])
                        rot_matrix = rotation_matrix(angle_xz, axis=UP)
                        label.points = np.dot(label.points, rot_matrix.T)

                    # 绕 RIGHT 轴旋转
                    horizontal_dist = np.sqrt(to_camera[0]**2 + to_camera[2]**2)
                    if horizontal_dist > 1e-6:
                        angle_elevation = np.arctan2(to_camera[1], horizontal_dist)
                        rot_matrix = rotation_matrix(angle_elevation, axis=RIGHT)
                        label.points = np.dot(label.points, rot_matrix.T)

                # 4. 修正镜像
                label.rotate(PI, axis=UP)

                # 5. 设置颜色和大小
                label.set_color(RED)
                label.scale(0.8)

        print("========== 场景构建完成 ==========\n")

        # ========== 静态场景，无动画 ==========


class CubeObliqueDemo(Scene):
    """
    斜二测画法（Oblique Projection）- 纯 2D 暴力绘图

    坐标定义（用户坐标系）：
    - u_x: 深度轴，指向屏幕左下方 45°
    - u_y: 水平轴，指向屏幕右侧
    - u_z: 竖直轴，指向屏幕上方

    技术实现：
    - 完全放弃 3D 和矩阵变换
    - 手动计算 8 个顶点的屏幕坐标
    - 使用 project() 函数投影
    - 手动绘制所有线条
    """

    def construct(self):
        # ========== 参数设置 ==========
        L = 2.5  # 正方体边长
        v = 0.5  # 斜二测缩短系数
        alpha = PI / 4  # 45°（弧度）

        # ========== 投影函数（核心算法）==========
        def project(u_x, u_y, u_z):
            """
            将用户坐标系投影到屏幕坐标

            参数：
            - u_x: 深度轴（左下 45°）
            - u_y: 水平轴（向右）
            - u_z: 竖直轴（向上）

            返回：
            - np.array([screen_x, screen_y, 0])
            """
            # 斜二测投影公式
            screen_x = u_y - u_x * v * np.cos(alpha)
            screen_y = u_z - u_x * v * np.sin(alpha)

            # 原点偏移（让图形居中）
            offset = LEFT * 2 + DOWN * 1

            return np.array([screen_x, screen_y, 0]) + offset

        print(f"\n========== 斜二测投影参数 ==========")
        print(f"边长 L = {L}")
        print(f"缩短系数 v = {v}")
        print(f"倾斜角度 α = {alpha / DEGREES}°")
        print(f"====================================\n")

        # ========== 定义 8 个顶点（用户坐标）==========
        # A(0,0,0) [原点]
        # B(L,0,0) [u_x 轴上，深度方向]
        # D(0,L,0) [u_y 轴上，水平向右]
        # A1(0,0,L) [u_z 轴上，竖直向上]

        vertices_user = {
            "A":  (0, 0, 0),
            "B":  (L, 0, 0),   # u_x 轴（深度，左下）
            "D":  (0, L, 0),   # u_y 轴（水平，向右）
            "C":  (L, L, 0),   # (u_x, u_y)
            "A1": (0, 0, L),   # u_z 轴（竖直，向上）
            "B1": (L, 0, L),   # (u_x, u_z)
            "D1": (0, L, L),   # (u_y, u_z)
            "C1": (L, L, L),   # (u_x, u_y, u_z)
        }

        # ========== 计算屏幕坐标 ==========
        vertices_screen = {}
        for name, (ux, uy, uz) in vertices_user.items():
            vertices_screen[name] = project(ux, uy, uz)
            print(f"{name}({ux},{uy},{uz}) -> {vertices_screen[name][:2]}")

        # ========== 绘制坐标轴（箭头）==========
        axes = VGroup()

        # x 轴（u_x，深度，左下 45°）
        x_axis = Arrow(
            start=vertices_screen["A"],
            end=project(L * 1.5, 0, 0),
            color=RED_E,
            buff=0,
            max_stroke_width_to_length_ratio=0.05
        )
        x_label = MathTex("x", font_size=24, color=RED_E)
        x_label.move_to(project(L * 1.7, 0, 0))
        axes.add(x_axis, x_label)

        # y 轴（u_y，水平，向右）
        y_axis = Arrow(
            start=vertices_screen["A"],
            end=project(0, L * 1.5, 0),
            color=GREEN_E,
            buff=0,
            max_stroke_width_to_length_ratio=0.05
        )
        y_label = MathTex("y", font_size=24, color=GREEN_E)
        y_label.move_to(project(0, L * 1.7, 0))
        axes.add(y_axis, y_label)

        # z 轴（u_z，竖直，向上）
        z_axis = Arrow(
            start=vertices_screen["A"],
            end=project(0, 0, L * 1.5),
            color=BLUE_E,
            buff=0,
            max_stroke_width_to_length_ratio=0.05
        )
        z_label = MathTex("z", font_size=24, color=BLUE_E)
        z_label.move_to(project(0, 0, L * 1.7))
        axes.add(z_axis, z_label)

        self.add(axes)

        # ========== 绘制棱边 ==========
        edges = VGroup()

        # 虚线（从原点 A 发散的三条棱，被遮挡）
        dashed_edges = [
            ("A", "B"),   # u_x 方向
            ("A", "D"),   # u_y 方向
            ("A", "A1"),  # u_z 方向
        ]

        for v1_name, v2_name in dashed_edges:
            line = DashedLine(
                start=vertices_screen[v1_name],
                end=vertices_screen[v2_name],
                color=GRAY,
                stroke_width=3,
                dash_length=0.15,
                stroke_opacity=0.6
            )
            edges.add(line)

        # 实线（其余 9 条棱）
        solid_edges = [
            ("B", "C"), ("C", "D"),      # 底面剩余边
            ("A1", "B1"), ("B1", "C1"), ("C1", "D1"), ("D1", "A1"),  # 顶面
            ("B", "B1"), ("C", "C1"), ("D", "D1"),  # 竖棱
        ]

        for v1_name, v2_name in solid_edges:
            line = Line(
                start=vertices_screen[v1_name],
                end=vertices_screen[v2_name],
                color=WHITE,
                stroke_width=3
            )
            edges.add(line)

        self.add(edges)

        # ========== 绘制顶点标签（手动偏移映射表）==========
        # 为每个顶点指定最佳偏移方向，避开从该点发出的射线（棱或坐标轴）

        # 定义偏移字典（方向向量）
        # 注意：Manim 的 UP/DOWN/LEFT/RIGHT 是单位向量
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

        # 紧凑距离参数（避免标签离顶点太远）
        default_buff = 0.25

        labels = VGroup()
        for name, pos in vertices_screen.items():
            if "1" in name:
                base_name = name[0]
                label = MathTex(base_name + "_1", font_size=28, color=YELLOW)
                label_name = name  # 使用原始键名（如 "A1", "B1"）
            else:
                label = MathTex(name, font_size=28, color=YELLOW)
                label_name = name

            # 获取对应的偏移方向
            direction = label_offsets.get(label_name, UP)

            # 应用偏移（顶点位置 + 方向 * 距离）
            label_pos = pos + direction * default_buff
            label.move_to(label_pos)

            # 调试输出
            print(f"{label_name}: offset={direction}, final_pos={label_pos[:2]}")

            labels.add(label)

        self.add(labels)

        # ========== 添加标题 ==========
        title = Text("斜二测画法（纯 2D 投影）", font_size=36)
        title.to_edge(UP)
        self.add(title)

        print(f"\n========== 渲染完成 ==========\n")


class ObliqueCubeComponentDemo(Scene):
    """
    斜二测正方体组件演示

    展示 ObliqueCube 组件的便捷使用方法
    """

    def construct(self):
        # ========== 使用组件创建斜二测正方体 ==========
        oblique_cube = ObliqueCube(
            side_length=2.5,
            shortening_factor=0.5,
            angle=PI / 4,  # 45°
            show_axes=True,
            show_labels=True,
            origin_offset=LEFT * 2 + DOWN * 1
        )

        # 添加到场景
        self.add(oblique_cube)

        # ========== 添加标题 ==========
        title = Text("斜二测正方体组件", font_size=36)
        title.to_edge(UP)
        self.add(title)

        # ========== 添加说明文字 ==========
        info = Text(
            "ObliqueCube 组件 - 标准教材画法",
            font_size=20,
            color=GRAY
        )
        info.next_to(title, DOWN)
        self.add(info)

        print("\n========== ObliqueCube 组件演示 ==========")
        print("组件已成功创建并渲染")
        print(f"边长: {oblique_cube.side_length}")
        print(f"缩短系数: {oblique_cube.shortening_factor}")
        print(f"倾斜角度: {oblique_cube.angle / DEGREES}°")
        print("========================================\n")


class CuboidObliqueDemo(Scene):
    """
    长方体斜二测画法（Oblique Projection for Cuboid）

    基于正方体斜二测场景，扩展为长宽高可自定义的长方体。

    坐标定义（用户坐标系）：
    - u_x: 深度轴，指向屏幕左下方 45°
    - u_y: 水平轴，指向屏幕右侧
    - u_z: 竖直轴，指向屏幕上方

    技术实现：
    - 完全复用正方体的投影函数和布局逻辑
    - 三个独立的棱长参数：a（深度）, b（宽度）, c（高度）
    - 相同的虚实线规则和标签偏移映射表
    """

    def construct(self):
        # ========== 自定义长方体棱长 ==========
        a = 3.0  # 深度（沿斜轴 X）
        b = 4.5  # 宽度（沿水平轴 Y）
        c = 2.0  # 高度（沿竖直轴 Z）

        # ========== 投影参数（与正方体完全相同）==========
        v = 0.5  # 斜二测缩短系数
        alpha = PI / 4  # 45°（弧度）

        # ========== 投影函数（完全复用）==========
        def project(u_x, u_y, u_z):
            """
            将用户坐标系投影到屏幕坐标

            参数：
            - u_x: 深度轴（左下 45°）
            - u_y: 水平轴（向右）
            - u_z: 竖直轴（向上）

            返回：
            - np.array([screen_x, screen_y, 0])
            """
            # 斜二测投影公式
            screen_x = u_y - u_x * v * np.cos(alpha)
            screen_y = u_z - u_x * v * np.sin(alpha)

            # 原点偏移（让图形居中）
            offset = LEFT * 2 + DOWN * 1

            return np.array([screen_x, screen_y, 0]) + offset

        print(f"\n========== 长方体斜二测投影参数 ==========")
        print(f"棱长: a={a} (深度), b={b} (宽度), c={c} (高度)")
        print(f"缩短系数 v = {v}")
        print(f"倾斜角度 α = {alpha / DEGREES}°")
        print(f"========================================\n")

        # ========== 定义 8 个顶点（基于 a,b,c）==========
        vertices_user = {
            "A":  (0, 0, 0),
            "B":  (a, 0, 0),   # u_x 轴（深度，左下）
            "D":  (0, b, 0),   # u_y 轴（水平，向右）
            "C":  (a, b, 0),   # (u_x, u_y)
            "A1": (0, 0, c),   # u_z 轴（竖直，向上）
            "B1": (a, 0, c),   # (u_x, u_z)
            "D1": (0, b, c),   # (u_y, u_z)
            "C1": (a, b, c),   # (u_x, u_y, u_z)
        }

        # ========== 计算屏幕坐标 ==========
        vertices_screen = {}
        for name, (ux, uy, uz) in vertices_user.items():
            vertices_screen[name] = project(ux, uy, uz)
            print(f"{name}({ux},{uy},{uz}) -> {vertices_screen[name][:2]}")

        # ========== 绘制坐标轴（箭头）==========
        axes = VGroup()

        # x 轴（u_x，深度，左下 45°）- 长度调整为 a * 1.3
        x_axis = Arrow(
            start=vertices_screen["A"],
            end=project(a * 1.3, 0, 0),
            color=RED_E,
            buff=0,
            max_stroke_width_to_length_ratio=0.05
        )
        x_label = MathTex("x", font_size=24, color=RED_E)
        x_label.move_to(project(a * 1.5, 0, 0))
        axes.add(x_axis, x_label)

        # y 轴（u_y，水平，向右）- 长度调整为 b * 1.3
        y_axis = Arrow(
            start=vertices_screen["A"],
            end=project(0, b * 1.3, 0),
            color=GREEN_E,
            buff=0,
            max_stroke_width_to_length_ratio=0.05
        )
        y_label = MathTex("y", font_size=24, color=GREEN_E)
        y_label.move_to(project(0, b * 1.5, 0))
        axes.add(y_axis, y_label)

        # z 轴（u_z，竖直，向上）- 长度调整为 c * 1.3
        z_axis = Arrow(
            start=vertices_screen["A"],
            end=project(0, 0, c * 1.3),
            color=BLUE_E,
            buff=0,
            max_stroke_width_to_length_ratio=0.05
        )
        z_label = MathTex("z", font_size=24, color=BLUE_E)
        z_label.move_to(project(0, 0, c * 1.5))
        axes.add(z_axis, z_label)

        self.add(axes)

        # ========== 绘制棱边（完全复用）==========
        edges = VGroup()

        # 虚线（从原点 A 发散的三条棱，被遮挡）
        dashed_edges = [
            ("A", "B"),   # u_x 方向
            ("A", "D"),   # u_y 方向
            ("A", "A1"),  # u_z 方向
        ]

        for v1_name, v2_name in dashed_edges:
            line = DashedLine(
                start=vertices_screen[v1_name],
                end=vertices_screen[v2_name],
                color=GRAY,
                stroke_width=3,
                dash_length=0.15,
                stroke_opacity=0.6
            )
            edges.add(line)

        # 实线（其余 9 条棱）
        solid_edges = [
            ("B", "C"), ("C", "D"),      # 底面剩余边
            ("A1", "B1"), ("B1", "C1"), ("C1", "D1"), ("D1", "A1"),  # 顶面
            ("B", "B1"), ("C", "C1"), ("D", "D1"),  # 竖棱
        ]

        for v1_name, v2_name in solid_edges:
            line = Line(
                start=vertices_screen[v1_name],
                end=vertices_screen[v2_name],
                color=WHITE,
                stroke_width=3
            )
            edges.add(line)

        self.add(edges)

        # ========== 绘制顶点标签（完全复用手动偏移映射表）==========
        # 定义偏移字典（方向向量）- 与正方体完全相同
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

        # 紧凑距离参数（与正方体完全相同）
        default_buff = 0.25

        labels = VGroup()
        for name, pos in vertices_screen.items():
            if "1" in name:
                base_name = name[0]
                label = MathTex(base_name + "_1", font_size=28, color=YELLOW)
                label_name = name
            else:
                label = MathTex(name, font_size=28, color=YELLOW)
                label_name = name

            # 获取对应的偏移方向
            direction = label_offsets.get(label_name, UP)

            # 应用偏移（顶点位置 + 方向 * 距离）
            label_pos = pos + direction * default_buff
            label.move_to(label_pos)

            labels.add(label)

        self.add(labels)

        # ========== 添加标题 ==========
        title = Text("长方体斜二测画法", font_size=36)
        title.to_edge(UP)
        self.add(title)

        # 添加尺寸标注
        dimensions = Text(f"a={a}, b={b}, c={c}", font_size=20, color=GRAY)
        dimensions.next_to(title, DOWN)
        self.add(dimensions)

        print(f"\n========== 渲染完成 ==========\n")


class PyramidObliqueDemo(Scene):
    """
    三棱锥斜二测画法（Oblique Projection for Pyramid）

    底面 ABC 在 xOy 平面上，顶点 D 在上方。
    A 为原点，AC 沿 User-Y 轴（水平向右），AB 沿 User-X 轴（深度，左下 45°）。

    坐标定义（用户坐标系）：
    - u_x: 深度轴，指向屏幕左下方 45°
    - u_y: 水平轴，指向屏幕右侧
    - u_z: 竖直轴，指向屏幕上方

    技术实现：
    - 完全复用正方体的投影函数和布局逻辑
    - 参数化控制底面边长和顶点位置
    - 相同的虚实线规则和标签偏移策略
    """

    def construct(self):
        # ========== 参数化控制 ==========
        # 底面边长
        len_AC = 4.0  # 底面宽度（沿 User-Y 轴）
        len_AB = 3.0  # 底面深度（沿 User-X 轴）

        # 顶点 D 坐标控制形状和二面角
        # D_x=0, D_y=0: AD 垂直于底面（正棱锥）
        # D_x > 0: 侧面沿 X 方向倾斜
        # D_y > 0: 侧面沿 Y 方向倾斜
        peak_x = 1.0  # 顶点 D 的 X 坐标（深度偏移）
        peak_y = 1.5  # 顶点 D 的 Y 坐标（宽度偏移）
        peak_z = 3.5  # 顶点 D 的 Z 坐标（高度）

        # ========== 投影参数（与正方体完全相同）==========
        v = 0.5  # 斜二测缩短系数
        alpha = PI / 4  # 45°（弧度）

        # ========== 投影函数（完全复用）==========
        def project(u_x, u_y, u_z):
            """
            将用户坐标系投影到屏幕坐标

            参数：
            - u_x: 深度轴（左下 45°）
            - u_y: 水平轴（向右）
            - u_z: 竖直轴（向上）

            返回：
            - np.array([screen_x, screen_y, 0])
            """
            # 斜二测投影公式
            screen_x = u_y - u_x * v * np.cos(alpha)
            screen_y = u_z - u_x * v * np.sin(alpha)

            # 原点偏移（让图形居中）
            offset = LEFT * 2 + DOWN * 1

            return np.array([screen_x, screen_y, 0]) + offset

        print(f"\n========== 三棱锥斜二测投影参数 ==========")
        print(f"底面边长: AC={len_AC} (宽度), AB={len_AB} (深度)")
        print(f"顶点 D 坐标: ({peak_x}, {peak_y}, {peak_z})")
        print(f"缩短系数 v = {v}")
        print(f"倾斜角度 α = {alpha / DEGREES}°")
        print(f"==========================================\n")

        # ========== 定义 4 个顶点 ==========
        vertices_user = {
            "A": (0, 0, 0),                        # 原点
            "B": (len_AB, 0, 0),                   # 在 User-X 轴（深度）
            "C": (0, len_AC, 0),                   # 在 User-Y 轴（宽度）
            "D": (peak_x, peak_y, peak_z),         # 顶点
        }

        # ========== 计算屏幕坐标 ==========
        vertices_screen = {}
        for name, (ux, uy, uz) in vertices_user.items():
            vertices_screen[name] = project(ux, uy, uz)
            print(f"{name}({ux},{uy},{uz}) -> {vertices_screen[name][:2]}")

        # ========== 绘制坐标轴（箭头）- 最底层 ==========
        # 坐标轴样式配置（更明亮、更粗）
        axis_config = {
            "stroke_width": 4,  # 加粗线条（默认 2-3）
            "max_tip_length_to_length_ratio": 0.15,
            "max_stroke_width_to_length_ratio": 5,
            "buff": 0
        }

        axes = VGroup()

        # x 轴（u_x，深度，左下 45°）- 使用亮红色
        x_axis = Arrow(
            start=vertices_screen["A"],
            end=project(len_AB * 1.3, 0, 0),
            color=RED_B,
            **axis_config
        )
        x_label = MathTex("x", font_size=24, color=RED_B)
        x_label.move_to(project(len_AB * 1.5, 0, 0))
        axes.add(x_axis, x_label)

        # y 轴（u_y，水平，向右）- 使用亮绿色
        y_axis = Arrow(
            start=vertices_screen["A"],
            end=project(0, len_AC * 1.3, 0),
            color=GREEN_B,
            **axis_config
        )
        y_label = MathTex("y", font_size=24, color=GREEN_B)
        y_label.move_to(project(0, len_AC * 1.5, 0))
        axes.add(y_axis, y_label)

        # z 轴（u_z，竖直，向上）- 使用亮蓝色
        z_axis = Arrow(
            start=vertices_screen["A"],
            end=project(0, 0, peak_z * 1.3),
            color=BLUE_B,
            **axis_config
        )
        z_label = MathTex("z", font_size=24, color=BLUE_B)
        z_label.move_to(project(0, 0, peak_z * 1.5))
        axes.add(z_axis, z_label)

        self.add(axes)  # Step 1: 添加坐标轴（底层）

        # ========== 绘制遮罩面 - 中间层 ==========
        # 创建四个面的遮罩，用于遮挡后方的坐标轴

        # 定义四个面的顶点索引
        face_indices = [
            ["A", "B", "C"],   # 底面
            ["A", "B", "D"],   # 侧面 1
            ["A", "C", "D"],   # 侧面 2
            ["B", "C", "D"],   # 侧面 3
        ]

        masks = VGroup()
        for indices in face_indices:
            # 获取面的顶点坐标
            points = [vertices_screen[idx] for idx in indices]

            # 创建黑色填充面（作为遮罩）
            face_mask = Polygon(
                *points,
                fill_color=BLACK,      # 与背景色一致
                fill_opacity=1.0,      # 完全不透明
                stroke_width=0         # 无描边
            )
            masks.add(face_mask)

        self.add(masks)  # Step 2: 添加遮罩面（中间层，盖住坐标轴）

        # ========== 绘制棱边 - 顶层 ==========
        edges = VGroup()

        # 虚线（从原点 A 发散的三条棱，被遮挡）
        # 这是标准的"墙角"三棱锥画法
        dashed_edges = [
            ("A", "B"),   # 底面深度棱
            ("A", "C"),   # 底面宽度棱
            ("A", "D"),   # 侧棱
        ]

        for v1_name, v2_name in dashed_edges:
            line = DashedLine(
                start=vertices_screen[v1_name],
                end=vertices_screen[v2_name],
                color=GRAY,
                stroke_width=3,
                dash_length=0.15,
                stroke_opacity=0.6
            )
            edges.add(line)

        # 实线（其余 3 条棱：外围轮廓）
        solid_edges = [
            ("B", "C"),   # 底面第三边
            ("B", "D"),   # 右侧棱
            ("C", "D"),   # 左侧棱
        ]

        for v1_name, v2_name in solid_edges:
            line = Line(
                start=vertices_screen[v1_name],
                end=vertices_screen[v2_name],
                color=WHITE,
                stroke_width=3
            )
            edges.add(line)

        self.add(edges)  # Step 3: 添加棱线（顶层，画在遮罩之上）

        # ========== 绘制顶点标签（手动偏移映射表）==========
        # 定义偏移字典（方向向量）
        label_offsets = {
            "A":  (LEFT + DOWN) * 0.5,     # 原点：左下（避开三条发散线）
            "B":  DOWN + LEFT,             # X 轴末端：左下
            "C":  DOWN + RIGHT,            # Y 轴末端：右下
            "D":  UP                       # 顶点：向上
        }

        # 紧凑距离参数
        default_buff = 0.25

        labels = VGroup()
        for name, pos in vertices_screen.items():
            label = MathTex(name, font_size=28, color=YELLOW)

            # 获取对应的偏移方向
            direction = label_offsets.get(name, UP)

            # 应用偏移（顶点位置 + 方向 * 距离）
            label_pos = pos + direction * default_buff
            label.move_to(label_pos)

            labels.add(label)

        self.add(labels)

        # ========== 添加标题 ==========
        title = Text("三棱锥斜二测画法", font_size=36)
        title.to_edge(UP)
        self.add(title)

        # 添加尺寸标注
        dimensions = Text(
            f"底面: {len_AC}×{len_AB}, 顶点: ({peak_x},{peak_y},{peak_z})",
            font_size=18,
            color=GRAY
        )
        dimensions.next_to(title, DOWN)
        self.add(dimensions)

        print(f"\n========== 渲染完成 ==========\n")


class GeneralQuadrangularPyramidDemo(Scene):
    """
    通用四棱锥斜二测画法（General Quadrangular Pyramid）

    底面为任意凸四边形，顶点 P 在上方。
    A 为原点，B, C, D 可自定义坐标。

    坐标定义（用户坐标系）：
    - u_x: 深度轴，指向屏幕左下方 45°
    - u_y: 水平轴，指向屏幕右侧
    - u_z: 竖直轴，指向屏幕上方

    技术实现：
    - 支持任意凸四边形底面
    - 完整的遮罩层（4 侧面 + 1 底面）
    - 相同的虚实线规则和标签偏移策略
    """

    def construct(self):
        # ========== 参数化控制：任意凸四边形 ==========
        # 顶点 P（Apex）
        peak_x = 0.5
        peak_y = 1.0
        peak_z = 4.0

        # 底面顶点坐标（A 固定在原点）
        # 注意：A, B, C, D 应按顺时针或逆时针顺序排列
        b_x, b_y = 3.0, 0.5   # B 点（向右偏一点）
        c_x, c_y = 2.5, 3.5   # C 点（斜向远处）
        d_x, d_y = 0.2, 2.0   # D 点（偏上一点）

        # ========== 投影参数（与之前相同）==========
        v = 0.5  # 斜二测缩短系数
        alpha = PI / 4  # 45°（弧度）

        # ========== 投影函数（完全复用）==========
        def project(u_x, u_y, u_z):
            """
            将用户坐标系投影到屏幕坐标

            参数：
            - u_x: 深度轴（左下 45°）
            - u_y: 水平轴（向右）
            - u_z: 竖直轴（向上）

            返回：
            - np.array([screen_x, screen_y, 0])
            """
            # 斜二测投影公式
            screen_x = u_y - u_x * v * np.cos(alpha)
            screen_y = u_z - u_x * v * np.sin(alpha)

            # 原点偏移（让图形居中）
            offset = LEFT * 2 + DOWN * 1

            return np.array([screen_x, screen_y, 0]) + offset

        print(f"\n========== 通用四棱锥斜二测投影参数 ==========")
        print(f"顶点 P 坐标: ({peak_x}, {peak_y}, {peak_z})")
        print(f"底面坐标: A(0,0,0), B({b_x},{b_y},0), C({c_x},{c_y},0), D({d_x},{d_y},0)")
        print(f"缩短系数 v = {v}")
        print(f"倾斜角度 α = {alpha / DEGREES}°")
        print(f"============================================\n")

        # ========== 定义 5 个顶点 ==========
        vertices_user = {
            "A": (0, 0, 0),
            "B": (b_x, b_y, 0),
            "C": (c_x, c_y, 0),
            "D": (d_x, d_y, 0),
            "P": (peak_x, peak_y, peak_z),
        }

        # ========== 计算屏幕坐标 ==========
        vertices_screen = {}
        for name, (ux, uy, uz) in vertices_user.items():
            vertices_screen[name] = project(ux, uy, uz)
            print(f"{name}({ux},{uy},{uz}) -> {vertices_screen[name][:2]}")

        # ========== 计算坐标轴长度（动态调整）==========
        # 根据底面顶点坐标确定轴长
        max_x = max(b_x, c_x, d_x, peak_x)
        max_y = max(b_y, c_y, d_y, peak_y)
        max_z = peak_z

        axis_length_x = max_x * 1.3 if max_x > 0 else 2.0
        axis_length_y = max_y * 1.3 if max_y > 0 else 2.0
        axis_length_z = max_z * 1.3 if max_z > 0 else 2.0

        # ========== 绘制坐标轴（箭头）- 最底层 ==========
        axis_config = {
            "stroke_width": 4,
            "max_tip_length_to_length_ratio": 0.15,
            "max_stroke_width_to_length_ratio": 5,
            "buff": 0
        }

        axes = VGroup()

        # x 轴（u_x，深度，左下 45°）- 使用亮红色
        x_axis = Arrow(
            start=vertices_screen["A"],
            end=project(axis_length_x, 0, 0),
            color=RED_B,
            **axis_config
        )
        x_label = MathTex("x", font_size=24, color=RED_B)
        x_label.move_to(project(axis_length_x * 1.15, 0, 0))
        axes.add(x_axis, x_label)

        # y 轴（u_y，水平，向右）- 使用亮绿色
        y_axis = Arrow(
            start=vertices_screen["A"],
            end=project(0, axis_length_y, 0),
            color=GREEN_B,
            **axis_config
        )
        y_label = MathTex("y", font_size=24, color=GREEN_B)
        y_label.move_to(project(0, axis_length_y * 1.15, 0))
        axes.add(y_axis, y_label)

        # z 轴（u_z，竖直，向上）- 使用亮蓝色
        z_axis = Arrow(
            start=vertices_screen["A"],
            end=project(0, 0, axis_length_z),
            color=BLUE_B,
            **axis_config
        )
        z_label = MathTex("z", font_size=24, color=BLUE_B)
        z_label.move_to(project(0, 0, axis_length_z * 1.15))
        axes.add(z_axis, z_label)

        self.add(axes)  # Step 1: 添加坐标轴（底层）

        # ========== 绘制遮罩面 - 中间层（4 侧面 + 1 底面）==========
        face_indices = [
            ["A", "B", "C", "D"],   # 底面
            ["A", "B", "P"],       # 侧面 1
            ["B", "C", "P"],       # 侧面 2
            ["C", "D", "P"],       # 侧面 3
            ["D", "A", "P"],       # 侧面 4
        ]

        masks = VGroup()
        for indices in face_indices:
            points = [vertices_screen[idx] for idx in indices]
            face_mask = Polygon(
                *points,
                fill_color=BLACK,
                fill_opacity=1.0,
                stroke_width=0
            )
            masks.add(face_mask)

        self.add(masks)  # Step 2: 添加遮罩面（中间层）

        # ========== 绘制棱边 - 顶层 ==========
        edges = VGroup()

        # 虚线（从原点 A 发散的三条棱 + PD + DC）
        dashed_edges = [
            ("A", "B"),   # 底面棱
            ("A", "D"),   # 底面棱
            ("A", "P"),   # 侧棱
            ("D", "C"),   # 底面棱
            ("P", "D"),   # 侧棱
        ]

        for v1_name, v2_name in dashed_edges:
            line = DashedLine(
                start=vertices_screen[v1_name],
                end=vertices_screen[v2_name],
                color=GRAY,
                stroke_width=3,
                dash_length=0.15,
                stroke_opacity=0.6
            )
            edges.add(line)

        # 实线（其余 3 条棱：外围轮廓）
        solid_edges = [
            ("B", "C"),   # 底面外沿
            ("B", "P"),   # 侧棱
            ("C", "P"),   # 侧棱
        ]

        for v1_name, v2_name in solid_edges:
            line = Line(
                start=vertices_screen[v1_name],
                end=vertices_screen[v2_name],
                color=WHITE,
                stroke_width=3
            )
            edges.add(line)

        self.add(edges)  # Step 3: 添加棱线（顶层）

        # ========== 绘制顶点标签（手动偏移映射表）==========
        label_offsets = {
            "A":  (LEFT + DOWN) * 0.5,     # 原点：左下
            "B":  DOWN + RIGHT * 0.5,      # B 点：右下
            "C":  RIGHT + DOWN,            # C 点：右
            "D":  UP + LEFT,               # D 点：左上
            "P":  UP                       # 顶点：向上
        }

        default_buff = 0.25

        labels = VGroup()
        for name, pos in vertices_screen.items():
            label = MathTex(name, font_size=28, color=YELLOW)

            direction = label_offsets.get(name, UP)
            label_pos = pos + direction * default_buff
            label.move_to(label_pos)

            labels.add(label)

        self.add(labels)  # Step 4: 添加标签（最顶层）

        # ========== 添加标题 ==========
        title = Text("通用四棱锥斜二测画法", font_size=36)
        title.to_edge(UP)
        self.add(title)

        # 添加说明
        info = Text(
            f"底面：任意凸四边形 ABCD",
            font_size=18,
            color=GRAY
        )
        info.next_to(title, DOWN)
        self.add(info)

        print(f"\n========== 渲染完成 ==========\n")


class CylinderObliqueDemo(Scene):
    """
    圆柱斜二测画法（Cylinder Oblique Projection）

    使用 CylinderOblique 组件进行演示（2D 拼装法）

    特性：
    - 2D 拼装法（直接用几何形状组装）
    - 分段坐标轴系统（内部虚线，外部实线）
    - 侧棱绝对垂直（两条竖直线）
    - 像在黑板上画图一样直观
    """

    def construct(self):
        # ========== 使用组件创建圆柱（2D 拼装法）==========
        cylinder = CylinderOblique(
            radius=2.0,
            height=3.5,
            skew_factor=0.4,  # 压缩比
            x_axis_angle=-135 * DEGREES,  # X 轴倾斜角度
            show_axes=True,
            show_labels=True
        )

        # 添加到场景
        self.add(cylinder)

        # ========== 添加半径标注 ==========
        # 直接使用右端点（2D 拼装法的优点）
        center_bottom = cylinder.get_center_bottom()
        left_bottom, right_bottom = cylinder.get_side_edge_points_bottom()

        radius_line = DashedLine(
            start=center_bottom,
            end=right_bottom,
            color=GRAY,
            stroke_width=2,
            stroke_opacity=0.8
        )
        self.add(radius_line)

        label_r = MathTex("r", font_size=20, color=GRAY)
        label_r.move_to((center_bottom + right_bottom) / 2 + UP * 0.3)
        self.add(label_r)

        # ========== 添加标题 ==========
        title = Text("圆柱斜二测画法", font_size=36)
        title.to_edge(UP)
        self.add(title)

        # 添加说明
        info = Text(
            f"半径: {cylinder.radius}, 高度: {cylinder.height}",
            font_size=18,
            color=GRAY
        )
        info.next_to(title, DOWN)
        self.add(info)

        print(f"\n========== 圆柱渲染完成 ==========")
        print(f"半径: {cylinder.radius}")
        print(f"高度: {cylinder.height}")
        print(f"压缩比: {cylinder.skew_factor}")
        print(f"X 轴角度: {cylinder.x_axis_angle / DEGREES}°")
        print(f"====================================\n")


class CylinderComponentDemo(Scene):
    """
    圆柱组件演示

    展示 CylinderOblique 组件的便捷使用方法
    """

    def construct(self):
        # ========== 使用组件创建斜二测圆柱（2D 拼装法）==========
        cylinder = CylinderOblique(
            radius=2.0,
            height=3.5,
            skew_factor=0.4,  # 压缩比（把圆压扁成椭圆）
            x_axis_angle=-135 * DEGREES,  # X 轴倾斜角度
            show_axes=True,
            show_labels=True
        )

        # 添加到场景
        self.add(cylinder)

        # ========== 添加标题 ==========
        title = Text("圆柱组件演示（2D 拼装法）", font_size=36)
        title.to_edge(UP)
        self.add(title)

        # ========== 添加说明文字 ==========
        info = Text(
            "CylinderOblique 组件 - 斜二测画法",
            font_size=20,
            color=GRAY
        )
        info.next_to(title, DOWN)
        self.add(info)

        print("\n========== CylinderOblique 组件演示 ==========")
        print("组件已成功创建并渲染")
        print(f"半径: {cylinder.radius}")
        print(f"高度: {cylinder.height}")
        print(f"压缩比: {cylinder.skew_factor}")
        print(f"X 轴角度: {cylinder.x_axis_angle / DEGREES}°")
        print("===============================================\n")



class ConeObliqueDemo(Scene):
    """
    圆锥斜二测画法（Cone Oblique Projection）

    使用 ConeOblique 组件进行演示

    特性：
    - 绝对中心构建法
    - 复用圆柱的完美逻辑
    - 侧棱为母线，连接底面端点与顶点
    - 标签 O（底面圆心）和 S（顶点）
    """

    def construct(self):
        # ========== 使用组件创建圆锥（绝对中心构建法）==========
        from components.solid_geometry.cone import ConeOblique
        
        cone = ConeOblique(
            radius=2.0,
            height=3.5,
            skew_factor=0.4,
            x_axis_angle=-135 * DEGREES,
            show_axes=True,
            show_labels=True
        )

        # 添加到场景
        self.add(cone)

        # ========== 添加半径标注 ==========
        center_bottom = cone.get_center_bottom()
        left_bottom, right_bottom = cone.get_side_edge_points_bottom()

        radius_line = DashedLine(
            start=center_bottom,
            end=right_bottom,
            color=GRAY,
            stroke_width=2,
            stroke_opacity=0.8
        )
        self.add(radius_line)

        label_r = MathTex("r", font_size=20, color=GRAY)
        label_r.move_to((center_bottom + right_bottom) / 2 + UP * 0.3)
        self.add(label_r)

        # ========== 添加高度标注 ==========
        apex = cone.get_apex()
        height_line = DashedLine(
            start=center_bottom,
            end=apex,
            color=GRAY,
            stroke_width=2,
            stroke_opacity=0.8
        )
        self.add(height_line)

        label_h = MathTex("h", font_size=20, color=GRAY)
        label_h.move_to((center_bottom + apex) / 2 + LEFT * 0.5)
        self.add(label_h)

        # ========== 添加标题 ==========
        title = Text("圆锥斜二测画法", font_size=36)
        title.to_edge(UP)
        self.add(title)

        # 添加说明
        info = Text(
            f"半径: {cone.radius}, 高度: {cone.height}",
            font_size=18,
            color=GRAY
        )
        info.next_to(title, DOWN)
        self.add(info)

        print(f"\n========== 圆锥渲染完成 ==========")
        print(f"半径: {cone.radius}")
        print(f"高度: {cone.height}")
        print(f"压缩比: {cone.skew_factor}")
        print(f"X 轴角度: {cone.x_axis_angle / DEGREES}°")
        print(f"====================================\n")


class FrustumObliqueDemo(Scene):
    """
    圆台斜二测画法（Frustum Oblique Projection）

    使用 FrustumOblique 组件进行演示

    特性：
    - 绝对中心构建法
    - 双半径系统（底面半径 R，顶面半径 r）
    - 侧棱连接上下对应端点
    - 标签 O（底面圆心）和 O'（顶面圆心）
    """

    def construct(self):
        # ========== 使用组件创建圆台（绝对中心构建法）==========
        from components.solid_geometry.frustum import FrustumOblique

        frustum = FrustumOblique(
            bottom_radius=2.0,   # 底面半径 R
            top_radius=1.0,      # 顶面半径 r
            height=3.0,          # 圆台高度
            skew_factor=0.4,     # 压缩比
            x_axis_angle=-135 * DEGREES,
            show_axes=True,
            show_labels=True
        )

        # 添加到场景
        self.add(frustum)

        # ========== 添加半径标注 ==========
        center_bottom = frustum.get_center_bottom()
        left_bottom, right_bottom = frustum.get_side_edge_points_bottom()

        # 底面半径标注
        radius_line_bottom = DashedLine(
            start=center_bottom,
            end=right_bottom,
            color=GRAY,
            stroke_width=2,
            stroke_opacity=0.8
        )
        self.add(radius_line_bottom)

        label_R = MathTex("R", font_size=20, color=GRAY)
        label_R.move_to((center_bottom + right_bottom) / 2 + DOWN * 0.3)
        self.add(label_R)

        # 顶面半径标注
        center_top = frustum.get_center_top()
        left_top, right_top = frustum.get_side_edge_points_top()

        radius_line_top = DashedLine(
            start=center_top,
            end=right_top,
            color=GRAY,
            stroke_width=2,
            stroke_opacity=0.8
        )
        self.add(radius_line_top)

        label_r = MathTex("r", font_size=20, color=GRAY)
        label_r.move_to((center_top + right_top) / 2 + UP * 0.3)
        self.add(label_r)

        # ========== 添加高度标注 ==========
        height_line = DashedLine(
            start=center_bottom,
            end=center_top,
            color=GRAY,
            stroke_width=2,
            stroke_opacity=0.8
        )
        self.add(height_line)

        label_h = MathTex("h", font_size=20, color=GRAY)
        label_h.move_to((center_bottom + center_top) / 2 + LEFT * 0.5)
        self.add(label_h)

        # ========== 添加标题 ==========
        title = Text("圆台斜二测画法", font_size=36)
        title.to_edge(UP)
        self.add(title)

        # 添加说明
        info = Text(
            f"底面半径 R: {frustum.bottom_radius}, 顶面半径 r: {frustum.top_radius}, 高度 h: {frustum.height}",
            font_size=18,
            color=GRAY
        )
        info.next_to(title, DOWN)
        self.add(info)

        # ========== 验证输出 ==========
        print(f"\n========== 圆台渲染完成 ==========")
        print(f"底面半径 R: {frustum.bottom_radius}")
        print(f"顶面半径 r: {frustum.top_radius}")
        print(f"高度 h: {frustum.height}")
        print(f"压缩比: {frustum.skew_factor}")
        print(f"X 轴角度: {frustum.x_axis_angle / DEGREES}°")

        # 验证关键点
        key_points = frustum.get_key_points()
        print(f"\n【关键点验证】")
        for name, point in key_points.items():
            print(f"  {name}: {np.round(point, 2)}")

        print(f"\n【侧棱验证】")
        left_edge_vector = frustum.left_edge.get_end() - frustum.left_edge.get_start()
        right_edge_vector = frustum.right_edge.get_end() - frustum.right_edge.get_start()
        left_edge_length = np.linalg.norm(left_edge_vector)
        right_edge_length = np.linalg.norm(right_edge_vector)

        print(f"  左侧棱长度: {left_edge_length:.4f}")
        print(f"  右侧棱长度: {right_edge_length:.4f}")

        if abs(left_edge_length - right_edge_length) < 0.01:
            print(f"  ✓ 两条侧棱长度相等（完美对称）")
        else:
            print(f"  ⚠ 两条侧棱长度不相等（偏差: {abs(left_edge_length - right_edge_length):.4f}）")

        print(f"====================================\n")


class TriangularPrismObliqueDemo(Scene):
    """
    直三棱柱斜二测画法（Triangular Prism Oblique Projection）

    使用 TriangularPrismOblique 组件进行演示

    特性：
    - 绝对中心构建法
    - 离散顶点连接法
    - 一个顶点在后（虚线），两个顶点在前（实线）
    - 标签 A,B,C（底面）和 A',B',C'（顶面）
    """

    def construct(self):
        # ========== 使用组件创建直三棱柱（绝对中心构建法）==========
        from components.solid_geometry.triangular_prism import TriangularPrismOblique

        prism = TriangularPrismOblique(
            side_radius=2.0,     # 外接圆半径
            height=3.5,          # 三棱柱高度
            skew_factor=0.4,     # 压缩比
            x_axis_angle=-135 * DEGREES,
            show_axes=True,
            show_labels=True
        )

        # 添加到场景
        self.add(prism)

        # ========== 添加外接圆标注（底面）==========
        center_bottom = prism.get_center_bottom()
        back_bottom, left_bottom, right_bottom = prism.get_vertices_bottom()

        # 绘制底面外接圆（虚线，用于展示顶点分布）
        from manim import Circle
        circumcircle = Circle(
            radius=prism.side_radius,
            color=GRAY,
            stroke_width=1,
            stroke_opacity=0.3
        )
        circumcircle.stretch(prism.skew_factor, dim=1, about_point=center_bottom)
        self.add(circumcircle)

        # ========== 添加高度标注 ==========
        center_top = prism.get_center_top()
        height_line = DashedLine(
            start=center_bottom,
            end=center_top,
            color=GRAY,
            stroke_width=2,
            stroke_opacity=0.8
        )
        self.add(height_line)

        label_h = MathTex("h", font_size=20, color=GRAY)
        label_h.move_to((center_bottom + center_top) / 2 + LEFT * 0.5)
        self.add(label_h)

        # ========== 添加标题 ==========
        title = Text("直三棱柱斜二测画法", font_size=36)
        title.to_edge(UP)
        self.add(title)

        # 添加说明
        info = Text(
            f"外接圆半径: {prism.side_radius}, 高度: {prism.height}",
            font_size=18,
            color=GRAY
        )
        info.next_to(title, DOWN)
        self.add(info)

        # ========== 验证输出 ==========
        print(f"\n========== 直三棱柱渲染完成 ==========")
        print(f"外接圆半径: {prism.side_radius}")
        print(f"高度 h: {prism.height}")
        print(f"压缩比: {prism.skew_factor}")
        print(f"X 轴角度: {prism.x_axis_angle / DEGREES}°")

        # 验证关键点
        key_points = prism.get_key_points()
        print(f"\n【关键点验证】")
        for name, point in key_points.items():
            print(f"  {name}: {np.round(point, 2)}")

        print(f"\n【顶点角度验证】")
        print(f"  后顶点 A 角度: {prism.angle_back / DEGREES}°")
        print(f"  左前顶点 B 角度: {prism.angle_left / DEGREES}°")
        print(f"  右前顶点 C 角度: {prism.angle_right / DEGREES}°")

        print(f"\n【侧棱验证】")
        # 直接使用计算好的顶点坐标
        back_edge_vector = prism.p_top_back - prism.p_bottom_back
        left_edge_vector = prism.p_top_left - prism.p_bottom_left
        right_edge_vector = prism.p_top_right - prism.p_bottom_right

        back_edge_length = np.linalg.norm(back_edge_vector)
        left_edge_length = np.linalg.norm(left_edge_vector)
        right_edge_length = np.linalg.norm(right_edge_vector)

        print(f"  后侧棱长度: {back_edge_length:.4f}")
        print(f"  左前侧棱长度: {left_edge_length:.4f}")
        print(f"  右前侧棱长度: {right_edge_length:.4f}")

        # 验证三条侧棱长度相等
        if (abs(back_edge_length - left_edge_length) < 0.01 and
            abs(left_edge_length - right_edge_length) < 0.01):
            print(f"  ✓ 三条侧棱长度相等（完美直棱柱）")
        else:
            print(f"  ⚠ 三条侧棱长度不完全相等")

        # 验证底面三角形边长
        bottom_bl = np.linalg.norm(prism.p_bottom_left - prism.p_bottom_back)
        bottom_br = np.linalg.norm(prism.p_bottom_right - prism.p_bottom_back)
        bottom_lr = np.linalg.norm(prism.p_bottom_right - prism.p_bottom_left)

        print(f"\n【底面三角形边长】")
        print(f"  后-左: {bottom_bl:.4f}")
        print(f"  后-右: {bottom_br:.4f}")
        print(f"  左-右: {bottom_lr:.4f}")

        # 验证是否为等边三角形
        if (abs(bottom_bl - bottom_br) < 0.01 and
            abs(bottom_br - bottom_lr) < 0.01):
            print(f"  ✓ 底面为等边三角形（外接圆半径正确）")
        else:
            print(f"  ⚠ 底面并非等边三角形")

        print(f"====================================\n")


class SphereObliqueDemo(Scene):
    """
    球体斜二测画法（Sphere Oblique Projection）

    使用 SphereOblique 组件进行演示

    特性：
    - 绝对中心构建法
    - 外轮廓永远是正圆
    - 赤道是水平椭圆，表现立体感
    - 坐标轴与球体表面的交点通过解析几何精确计算
    - 标签 O（球心）和 N（北极点）
    """

    def construct(self):
        # ========== 使用组件创建球体（绝对中心构建法）==========
        from components.solid_geometry.sphere import SphereOblique

        sphere = SphereOblique(
            radius=2.0,         # 球体半径
            skew_factor=0.3,    # 压缩比（赤道椭圆扁度）
            x_axis_angle=-135 * DEGREES,
            show_axes=True,
            show_labels=True
        )

        # 添加到场景
        self.add(sphere)

        # ========== 添加半径标注（可选）==========
        center = sphere.get_center()
        north_pole = sphere.get_north_pole()

        radius_line = DashedLine(
            start=center,
            end=north_pole,
            color=GRAY,
            stroke_width=2,
            stroke_opacity=0.8
        )
        self.add(radius_line)

        label_R = MathTex("R", font_size=20, color=GRAY)
        label_R.move_to((center + north_pole) / 2 + LEFT * 0.5)
        self.add(label_R)

        # ========== 添加标题 ==========
        title = Text("球体斜二测画法", font_size=36)
        title.to_edge(UP)
        self.add(title)

        # 添加说明
        info = Text(
            f"半径 R: {sphere.radius}, 压缩比: {sphere.skew_factor}",
            font_size=18,
            color=GRAY
        )
        info.next_to(title, DOWN)
        self.add(info)

        # ========== 验证输出 ==========
        print(f"\n========== 球体渲染完成 ==========")
        print(f"半径 R: {sphere.radius}")
        print(f"压缩比: {sphere.skew_factor}")
        print(f"X 轴角度: {sphere.x_axis_angle / DEGREES}°")

        # 验证关键点
        key_points = sphere.get_key_points()
        print(f"\n【关键点验证】")
        for name, point in key_points.items():
            print(f"  {name}: {np.round(point, 2)}")

        # 验证 X 轴交点计算
        if 'p_x_intersect' in key_points:
            print(f"\n【X 轴交点计算验证】")
            # 椭圆参数
            a = sphere.radius
            b = sphere.radius * sphere.skew_factor
            k = np.tan(sphere.x_axis_angle)

            # 计算理论交点
            x_intersect_theory = - (a * b) / np.sqrt(b**2 + a**2 * k**2)
            y_intersect_theory = k * x_intersect_theory

            # 实际交点
            p_x_intersect = key_points['p_x_intersect']
            x_intersect_actual = p_x_intersect[0] - sphere.p_center[0]
            y_intersect_actual = p_x_intersect[1] - sphere.p_center[1]

            print(f"  理论 x 坐标: {x_intersect_theory:.4f}")
            print(f"  实际 x 坐标: {x_intersect_actual:.4f}")
            print(f"  理论 y 坐标: {y_intersect_theory:.4f}")
            print(f"  实际 y 坐标: {y_intersect_actual:.4f}")

            if (abs(x_intersect_theory - x_intersect_actual) < 0.01 and
                abs(y_intersect_theory - y_intersect_actual) < 0.01):
                print(f"  ✓ X 轴交点计算正确（解析几何验证通过）")
            else:
                print(f"  ⚠ X 轴交点计算有偏差")

            # 验证交点是否在椭圆上
            ellipse_value = (x_intersect_actual**2 / a**2 +
                           y_intersect_actual**2 / b**2)
            print(f"  椭圆方程值: {ellipse_value:.6f}（应该 ≈ 1）")

            if abs(ellipse_value - 1.0) < 0.01:
                print(f"  ✓ 交点在椭圆上（几何验证通过）")
            else:
                print(f"  ⚠ 交点不在椭圆上")

        # 验证坐标轴长度
        print(f"\n【坐标轴长度验证】")
        if 'p_y_intersect' in key_points and 'p_z_intersect' in key_points:
            y_axis_length = np.linalg.norm(key_points['p_y_intersect'] - sphere.p_center)
            z_axis_length = np.linalg.norm(key_points['p_z_intersect'] - sphere.p_center)

            print(f"  Y 轴长度（球内）: {y_axis_length:.4f}")
            print(f"  Z 轴长度（球内）: {z_axis_length:.4f}")

            if abs(y_axis_length - sphere.radius) < 0.01:
                print(f"  ✓ Y 轴长度等于半径")
            else:
                print(f"  ⚠ Y 轴长度不等于半径")

            if abs(z_axis_length - sphere.radius) < 0.01:
                print(f"  ✓ Z 轴长度等于半径")
            else:
                print(f"  ⚠ Z 轴长度不等于半径")

        print(f"====================================\n")

