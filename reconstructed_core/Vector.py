"""
Manim Vector 类重构版 - 多模态视觉数据集专用

改动说明：
1. 环境净化：移除所有交互式调试逻辑和本地文件依赖
2. 数据集安全：确保 Bbox 稳定，避免不可见对象占位
3. 语义标签注入：强制添加三个语义属性
4. 力学分析预设：为高中力学受力分析预设语义角色
"""

import math
import numpy as np
from typing import Optional, Tuple, Union

from manimlib.constants import (
    LEFT, RIGHT, UP, DOWN, ORIGIN, OUT,
    DEFAULT_LIGHT_COLOR, BLUE, RED, YELLOW, GREEN, WHITE,
    PI, DEGREES, MED_SMALL_BUFF
)
from manimlib.mobject.types.vectorized_mobject import VMobject, VGroup
from manimlib.utils.space_ops import (
    normalize, get_norm, rotate_vector, angle_of_vector,
    rotation_matrix_transpose
)
from manimlib.utils.bezier import quadratic_bezier_points_for_arc
from manimlib.utils.simple_functions import fdiv


# 类型定义
Vect3 = np.ndarray
ManimColor = str  # 简化类型定义


class Line(VMobject):
    """
    重构版 Line 类 - 几何直线基础类

    改动点：
    - 移除 TipableVMobject 依赖，简化继承链
    - 移除 add_tip 等交互式方法，专注纯几何绘制
    - 确保 set_points_by_ends 不会产生内部 ID 变化
    """

    def __init__(
        self,
        start: Vect3 = LEFT,
        end: Vect3 = RIGHT,
        buff: float = 0.0,
        path_arc: float = 0.0,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.path_arc = path_arc
        self.buff = buff
        self.set_start_and_end_attrs(start, end)
        self.set_points_by_ends(self.start, self.end, buff, path_arc)

    def set_points_by_ends(
        self,
        start: Vect3,
        end: Vect3,
        buff: float = 0,
        path_arc: float = 0
    ) -> 'Line':
        """通过起点和终点设置线条点 - 确保内部点结构稳定"""
        self.clear_points()
        self.start_new_path(start)
        self.add_arc_to(end, path_arc)

        # 应用缓冲区（数据集安全：避免产生零长度对象）
        if buff > 0:
            length = self.get_arc_length()
            alpha = min(buff / length, 0.5)
            self.pointwise_become_partial(self, alpha, 1 - alpha)
        return self

    def reset_points_around_ends(self) -> 'Line':
        """重置点 - 保持内部点结构一致，避免 Bbox 波动"""
        self.set_points_by_ends(
            self.get_start().copy(),
            self.get_end().copy(),
            path_arc=self.path_arc
        )
        return self

    def set_start_and_end_attrs(
        self,
        start: Union['Mobject', Vect3],
        end: Union['Mobject', Vect3]
    ):
        """设置起点和终点属性 - 统一为点坐标"""
        rough_start = self._pointify(start)
        rough_end = self._pointify(end)
        vect = normalize(rough_end - rough_start)
        self.start = self._pointify(start, vect)
        self.end = self._pointify(end, -vect)

    def _pointify(
        self,
        mob_or_point: Union['Mobject', Vect3],
        direction: Optional[Vect3] = None
    ) -> Vect3:
        """将对象或点统一转换为坐标点"""
        if isinstance(mob_or_point, (np.ndarray, list, tuple)):
            return np.array(mob_or_point, dtype=float)
        else:
            # 数据集安全：直接返回中心点，不进行边界计算
            # 避免因对象边界变化导致的 Bbox 不稳定
            return mob_or_point.get_center()

    def get_start(self) -> Vect3:
        """获取线条起点"""
        points = self.get_points()
        if len(points) == 0:
            return ORIGIN
        return points[0]

    def get_end(self) -> Vect3:
        """获取线条终点"""
        points = self.get_points()
        if len(points) == 0:
            return ORIGIN
        return points[-1]

    def get_vector(self) -> Vect3:
        """获取向量（终点 - 起点）"""
        return self.get_end() - self.get_start()

    def get_unit_vector(self) -> Vect3:
        """获取单位向量"""
        return normalize(self.get_vector())

    def get_angle(self) -> float:
        """获取角度"""
        return angle_of_vector(self.get_vector())

    def get_start_and_end(self) -> Tuple[Vect3, Vect3]:
        """获取起点和终点 - 用于 Bbox 计算"""
        return (self.get_start(), self.get_end())

    def put_start_and_end_on(
        self,
        start: Vect3,
        end: Vect3
    ) -> 'Line':
        """将线条端点放到指定位置 - 保持内部结构稳定"""
        self.set_points_by_ends(start, end, buff=0, path_arc=self.path_arc)
        return self

    def scale(self, *args, **kwargs) -> 'Line':
        """缩放线条 - 重置端点以确保 Bbox 稳定"""
        super().scale(*args, **kwargs)
        self.reset_points_around_ends()
        return self


class Arrow(Line):
    """
    重构版 Arrow 类 - 带箭头的线条

    改动点：
    - 重写 set_points_by_ends，使用填充箭头而非添加子对象
    - 避免使用不可见对象占位
    - 确保箭头几何完全包含在单个 VMobject 中
    """

    # 数据集安全：使用默认值避免外部依赖
    thickness_multiplier = 0.015

    def __init__(
        self,
        start: Union['Mobject', Vect3] = LEFT,
        end: Union['Mobject', Vect3] = RIGHT,
        buff: float = MED_SMALL_BUFF,
        path_arc: float = 0.0,
        fill_color: ManimColor = DEFAULT_LIGHT_COLOR,
        fill_opacity: float = 1.0,
        stroke_width: float = 0.0,
        thickness: float = 3.0,
        tip_width_ratio: float = 5.0,
        tip_angle: float = PI / 3,
        max_tip_length_to_length_ratio: float = 0.5,
        max_width_to_length_ratio: float = 0.1,
        **kwargs
    ):
        # 初始化几何参数
        self.thickness = thickness
        self.tip_width_ratio = tip_width_ratio
        self.tip_angle = tip_angle
        self.max_tip_length_to_length_ratio = max_tip_length_to_length_ratio
        self.max_width_to_length_ratio = max_width_to_length_ratio

        super().__init__(
            start, end,
            fill_color=fill_color,
            fill_opacity=fill_opacity,
            stroke_width=stroke_width,
            buff=buff,
            path_arc=path_arc,
            **kwargs
        )

    def get_key_dimensions(self, length: float) -> Tuple[float, float, float]:
        """计算箭头关键尺寸 - 确保尺寸稳定"""
        width = self.thickness * self.thickness_multiplier
        w_ratio = fdiv(self.max_width_to_length_ratio, fdiv(width, length))
        if w_ratio < 1:
            width *= w_ratio

        tip_width = self.tip_width_ratio * width
        tip_length = tip_width / (2 * np.tan(self.tip_angle / 2))
        t_ratio = fdiv(self.max_tip_length_to_length_ratio, fdiv(tip_length, length))
        if t_ratio < 1:
            tip_length *= t_ratio
            tip_width *= t_ratio

        return width, tip_width, tip_length

    def set_points_by_ends(
        self,
        start: Vect3,
        end: Vect3,
        buff: float = 0,
        path_arc: float = 0
    ) -> 'Arrow':
        """
        设置箭头的几何点 - 核心绘制逻辑

        改动点：
        - 使用填充箭头而非添加子对象，避免内部 ID 变化
        - 所有点都存储在单个 VMobject 中，确保 Bbox 稳定
        - 不使用任何不可见对象占位
        """
        vect = end - start
        length = max(get_norm(vect), 1e-8)  # 避免除零
        unit_vect = normalize(vect)

        # 计算箭头尺寸
        width, tip_width, tip_length = self.get_key_dimensions(length - buff)

        # 根据 buff 调整起点和终点
        if path_arc == 0:
            start = start + buff * unit_vect
            end = end - buff * unit_vect
        else:
            # 弧形箭头的处理
            R = length / 2 / math.sin(path_arc / 2)
            midpoint = 0.5 * (start + end)
            center = midpoint + rotate_vector(0.5 * vect, PI / 2) / math.tan(path_arc / 2)
            start = center + rotate_vector(start - center, buff / R)
            end = center + rotate_vector(end - center, -buff / R)
            path_arc -= (2 * buff + tip_length) / R
        vect = end - start
        length = get_norm(vect)

        # 创建箭杆的点
        if path_arc == 0:
            # 直线箭杆
            points1 = (length - tip_length) * np.array([RIGHT, 0.5 * RIGHT, ORIGIN])
            points1 += width * UP / 2
            points2 = points1[::-1] + width * DOWN
        else:
            # 曲线箭杆
            points1 = quadratic_bezier_points_for_arc(path_arc)
            points2 = np.array(points1[::-1])
            points1 *= (R + width / 2)
            points2 *= (R - width / 2)
            rot_T = rotation_matrix_transpose(PI / 2 - path_arc, OUT)
            for points in points1, points2:
                points[:] = np.dot(points, rot_T)
                points += R * DOWN

        # 设置箭杆点
        self.set_points(points1)

        # 添加箭头尖端（数据集安全：所有点都在同一对象中）
        self.add_line_to(tip_width * UP / 2)
        self.add_line_to(tip_length * LEFT)
        self.tip_index = len(self.get_points()) - 1
        self.add_line_to(tip_width * DOWN / 2)
        self.add_line_to(points2[0])

        # 闭合路径
        self.add_subpath(points2)
        self.add_line_to(points1[0])

        # 定位和旋转
        self.rotate(angle_of_vector(vect) - self.get_angle())
        self.rotate(
            PI / 2 - np.arccos(normalize(vect)[2]),
            axis=rotate_vector(self.get_unit_vector(), -PI / 2),
        )
        self.shift(start - self.get_start())

        return self

    def get_start(self) -> Vect3:
        """获取箭头起点"""
        points = self.get_points()
        return 0.5 * (points[0] + points[-3])

    def get_end(self) -> Vect3:
        """获取箭头终点（箭头尖端）"""
        return self.get_points()[self.tip_index]

    def set_thickness(self, thickness: float) -> 'Arrow':
        """设置箭头粗细"""
        self.thickness = thickness
        self.reset_points_around_ends()
        return self


class Vector(Arrow):
    """
    重构版 Vector 类 - 物理向量对象

    改动点：
    - 强制注入三个语义标签属性
    - 为高中力学受力分析预设语义角色
    - 确保从原点出发，符合物理向量定义
    - 提供语义设置接口，方便数据集生成

    语义标签说明：
    - semantic_type: 视觉类型，用于识别对象类别
    - semantic_role: 物理/数学含义，用于识别力/速度/加速度等
    - semantic_content: LaTeX 公式或关键数值，用于标注
    """

    # 力学分析预设的语义类型
    SEMANTIC_TYPES = {
        'force': 'force_vector',
        'velocity': 'velocity_vector',
        'acceleration': 'acceleration_vector',
        'displacement': 'displacement_vector',
        'custom': 'custom_vector'
    }

    # 力学分析预设的语义角色
    SEMANTIC_ROLES = {
        # 力学受力分析角色
        'gravity': 'gravitational_force',
        'normal': 'normal_force',
        'friction': 'friction_force',
        'tension': 'tension_force',
        'applied': 'applied_force',
        'spring': 'spring_force',
        'electric': 'electric_field',
        'magnetic': 'magnetic_field',
        # 运动学角色
        'velocity': 'velocity_vector',
        'acceleration': 'acceleration_vector',
        # 通用角色
        'unknown': 'unknown_force',
        'custom': 'custom_role'
    }

    def __init__(
        self,
        direction: Vect3 = RIGHT,
        buff: float = 0.0,
        # 语义标签参数（数据集核心）
        semantic_type: str = 'force',
        semantic_role: str = 'applied',
        semantic_content: str = '',
        # 物理属性
        magnitude: Optional[float] = None,
        color_map: Optional[dict] = None,
        **kwargs
    ):
        """
        初始化向量对象

        Args:
            direction: 向量方向（从原点出发）
            buff: 缓冲区距离
            semantic_type: 语义类型（force/velocity/acceleration等）
            semantic_role: 语义角色（gravity/normal/friction等）
            semantic_content: 语义内容（LaTeX公式或数值）
            magnitude: 向量大小（用于标注）
            color_map: 自定义颜色映射（覆盖默认值）
            **kwargs: 其他 Arrow 参数
        """
        # 确保方向是3D向量
        if len(direction) == 2:
            direction = np.hstack([direction, 0])

        # 初始化父类（数据集安全：buff=0，避免端点调整导致 Bbox 不稳定）
        super().__init__(ORIGIN, direction, buff=buff, **kwargs)

        # 【数据集安全】强制注入三个语义标签属性
        self._semantic_type = semantic_type
        self._semantic_role = semantic_role
        self._semantic_content = semantic_content
        self._magnitude = magnitude
        self._color_map = color_map or self._get_default_color_map()

        # 应用语义颜色（数据集安全：颜色与语义一致）
        self._apply_semantic_color()

    def _get_default_color_map(self) -> dict:
        """
        获取默认颜色映射 - 力学分析标准配色

        改动点：
        - 使用 Manim 标准颜色，不依赖自定义调色板
        - 颜色与语义角色对应，便于视觉识别
        """
        return {
            'gravity': YELLOW,
            'normal': BLUE,
            'friction': RED,
            'tension': GREEN,
            'applied': BLUE,
            'spring': GREEN,
            'electric': RED,
            'magnetic': BLUE,
            'velocity': GREEN,
            'acceleration': RED,
            'unknown': WHITE,
            'custom': DEFAULT_LIGHT_COLOR
        }

    def _apply_semantic_color(self):
        """应用语义颜色 - 确保颜色与语义一致"""
        color = self._color_map.get(self._semantic_role, DEFAULT_LIGHT_COLOR)
        self.set_fill(color)

    # ========== 语义标签接口（外部访问） ==========

    @property
    def semantic_type(self) -> str:
        """获取语义类型"""
        return self._semantic_type

    @semantic_type.setter
    def semantic_type(self, value: str):
        """
        设置语义类型

        改动点：
        - 类型检查，确保使用预定义类型
        - 自动更新颜色以匹配新类型
        """
        if value not in self.SEMANTIC_TYPES:
            raise ValueError(
                f"Invalid semantic_type: {value}. "
                f"Must be one of {list(self.SEMANTIC_TYPES.keys())}"
            )
        self._semantic_type = value
        self._apply_semantic_color()

    @property
    def semantic_role(self) -> str:
        """获取语义角色"""
        return self._semantic_role

    @semantic_role.setter
    def semantic_role(self, value: str):
        """
        设置语义角色

        改动点：
        - 角色检查，确保使用预定义角色
        - 自动更新颜色以匹配新角色
        """
        if value not in self.SEMANTIC_ROLES:
            raise ValueError(
                f"Invalid semantic_role: {value}. "
                f"Must be one of {list(self.SEMANTIC_ROLES.keys())}"
            )
        self._semantic_role = value
        self._apply_semantic_color()

    @property
    def semantic_content(self) -> str:
        """获取语义内容"""
        return self._semantic_content

    @semantic_content.setter
    def semantic_content(self, value: str):
        """设置语义内容（LaTeX公式或数值）"""
        self._semantic_content = value

    @property
    def magnitude(self) -> Optional[float]:
        """获取向量大小"""
        return self._magnitude

    @magnitude.setter
    def magnitude(self, value: float):
        """设置向量大小"""
        self._magnitude = value
        # 更新语义内容（数据集安全：内容与数值一致）
        if not self._semantic_content:
            self.semantic_content = f"{value} N" if self._semantic_type == 'force' else str(value)

    # ========== 力学分析快捷方法 ==========

    def as_force(self, force_type: str = 'applied', magnitude: float = 0) -> 'Vector':
        """
        设置为力向量

        Args:
            force_type: 力的类型（gravity/normal/friction等）
            magnitude: 力的大小

        Returns:
            self，支持链式调用
        """
        self.semantic_type = 'force'
        self.semantic_role = force_type
        if magnitude > 0:
            self.magnitude = magnitude
        return self

    def as_gravity(self, magnitude: float = 9.8) -> 'Vector':
        """设置为重力向量"""
        return self.as_force('gravity', magnitude)

    def as_normal(self, magnitude: float = 0) -> 'Vector':
        """设置为支持力向量"""
        return self.as_force('normal', magnitude)

    def as_friction(self, magnitude: float = 0) -> 'Vector':
        """设置为摩擦力向量"""
        return self.as_force('friction', magnitude)

    def as_tension(self, magnitude: float = 0) -> 'Vector':
        """设置为拉力向量"""
        return self.as_force('tension', magnitude)

    def as_applied(self, magnitude: float = 0) -> 'Vector':
        """设置为外力向量"""
        return self.as_force('applied', magnitude)

    def as_velocity(self, magnitude: float = 0) -> 'Vector':
        """设置为速度向量"""
        self.semantic_type = 'velocity'
        self.semantic_role = 'velocity'
        if magnitude > 0:
            self.magnitude = magnitude
        return self

    def as_acceleration(self, magnitude: float = 0) -> 'Vector':
        """设置为加速度向量"""
        self.semantic_type = 'acceleration'
        self.semantic_role = 'acceleration'
        if magnitude > 0:
            self.magnitude = magnitude
        return self

    # ========== 数据集安全方法 ==========

    def get_bbox(self) -> Tuple[Vect3, Vect3]:
        """
        获取包围盒 - 用于数据集生成

        改动点：
        - 重写父类方法，确保 Bbox 计算稳定
        - 避免因内部结构变化导致的 Bbox 波动
        """
        points = self.get_points()
        if len(points) == 0:
            return ORIGIN.copy(), ORIGIN.copy()
        return points.min(axis=0), points.max(axis=0)

    def copy(self, **kwargs) -> 'Vector':
        """
        复制向量对象 - 保留所有语义标签

        改动点：
        - 确保复制时保留语义属性
        - 用于数据集批量生成场景
        """
        new_vector = super().copy(**kwargs)
        new_vector._semantic_type = self._semantic_type
        new_vector._semantic_role = self._semantic_role
        new_vector._semantic_content = self._semantic_content
        new_vector._magnitude = self._magnitude
        new_vector._color_map = self._color_map.copy()
        return new_vector

    def set_direction(self, direction: Vect3) -> 'Vector':
        """
        设置向量方向

        改动点：
        - 保持起点在原点，符合物理向量定义
        - 确保内部点结构稳定
        """
        if len(direction) == 2:
            direction = np.hstack([direction, 0])
        self.put_start_and_end_on(ORIGIN, direction)
        return self

    def get_direction(self) -> Vect3:
        """获取向量方向（归一化）"""
        start, end = self.get_start_and_end()
        return normalize(end - start)

    def get_length(self) -> float:
        """获取向量长度"""
        return get_norm(self.get_direction() * np.linalg.norm(self.get_end() - self.get_start()))


# ========== 高中力学受力分析常用快捷函数 ==========

def GravityVector(
    direction: Vect3 = DOWN,
    magnitude: float = 9.8
) -> Vector:
    """快捷创建重力向量"""
    return Vector(direction).as_gravity(magnitude)


def NormalVector(
    direction: Vect3 = UP,
    magnitude: float = 0
) -> Vector:
    """快捷创建支持力向量"""
    return Vector(direction).as_normal(magnitude)


def FrictionVector(
    direction: Vect3 = LEFT,
    magnitude: float = 0
) -> Vector:
    """快捷创建摩擦力向量"""
    return Vector(direction).as_friction(magnitude)


def TensionVector(
    direction: Vect3 = RIGHT,
    magnitude: float = 0
) -> Vector:
    """快捷创建拉力向量"""
    return Vector(direction).as_tension(magnitude)


def AppliedForceVector(
    direction: Vect3 = RIGHT,
    magnitude: float = 0
) -> Vector:
    """快捷创建外力向量"""
    return Vector(direction).as_applied(magnitude)


def VelocityVector(
    direction: Vect3 = RIGHT,
    magnitude: float = 0
) -> Vector:
    """快捷创建速度向量"""
    return Vector(direction).as_velocity(magnitude)


def AccelerationVector(
    direction: Vect3 = RIGHT,
    magnitude: float = 0
) -> Vector:
    """快捷创建加速度向量"""
    return Vector(direction).as_acceleration(magnitude)
