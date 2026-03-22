from __future__ import annotations

from typing import Iterable, Optional, Sequence, Tuple, Union

import numpy as np
from manimlib import *


class Axes(VGroup):
    """面向数据集标注场景清洗后的二维坐标轴组件。"""

    def __init__(
        self,
        x_range: Optional[Sequence[float]] = None,
        y_range: Optional[Sequence[float]] = None,
        axis_config: Optional[dict] = None,
        x_axis_config: Optional[dict] = None,
        y_axis_config: Optional[dict] = None,
        height: Optional[float] = 6.0,
        width: Optional[float] = 10.0,
        unit_size: Optional[float] = None,
        semantic_type: str = "coordinate_system",
        semantic_role: str = "standard_axes",
        semantic_content: Optional[str] = "x-y axes",
        **kwargs
    ):
        super().__init__(**kwargs)
        self._semantic_type = ""
        self._semantic_role = ""
        self._semantic_content = None

        self.semantic_type = semantic_type
        self.semantic_role = semantic_role
        self.semantic_content = semantic_content

        self.x_range = self._normalize_range(x_range, default=(-6.0, 6.0, 1.0))
        self.y_range = self._normalize_range(y_range, default=(-4.0, 4.0, 1.0))

        base_axis_config = {
            "include_tip": True,
            "include_numbers": False,
            "stroke_width": 2,
            "color": BLACK,
        }
        if axis_config:
            base_axis_config.update(dict(axis_config))

        self._width = float(width) if width is not None else None
        self._height = float(height) if height is not None else None
        self._unit_size = float(unit_size) if unit_size is not None else None

        x_cfg = dict(base_axis_config)
        if x_axis_config:
            x_cfg.update(dict(x_axis_config))

        y_cfg = dict(base_axis_config)
        if y_axis_config:
            y_cfg.update(dict(y_axis_config))

        x_length = self._resolve_axis_length(self.x_range, self._width, self._unit_size)
        y_length = self._resolve_axis_length(self.y_range, self._height, self._unit_size)

        self.x_axis = self.create_axis(self.x_range, x_cfg, x_length)
        self.y_axis = self.create_axis(self.y_range, y_cfg, y_length)

        self.y_axis.rotate(np.pi / 2, about_point=self.y_axis.n2p(0))

        x_origin = self.x_axis.n2p(0)
        y_origin = self.y_axis.n2p(0)
        self.y_axis.shift(x_origin - y_origin)

        self.axes = VGroup(self.x_axis, self.y_axis)
        self.add(self.axes)

        self.coordinate_labels = VGroup()
        self._bbox_cache = None
        self._bbox_signature = None

    @property
    def semantic_type(self) -> str:
        return self._semantic_type

    @semantic_type.setter
    def semantic_type(self, value: str) -> None:
        if not isinstance(value, str):
            raise TypeError("semantic_type 必须是字符串")
        if not value.strip():
            raise ValueError("semantic_type 不能为空字符串")
        self._semantic_type = value

    @property
    def semantic_role(self) -> str:
        return self._semantic_role

    @semantic_role.setter
    def semantic_role(self, value: str) -> None:
        if not isinstance(value, str):
            raise TypeError("semantic_role 必须是字符串")
        if not value.strip():
            raise ValueError("semantic_role 不能为空字符串")
        self._semantic_role = value

    @property
    def semantic_content(self) -> Optional[str]:
        return self._semantic_content

    @semantic_content.setter
    def semantic_content(self, value: Optional[str]) -> None:
        if value is not None and not isinstance(value, str):
            raise TypeError("semantic_content 必须是字符串或 None")
        if isinstance(value, str) and not value.strip():
            raise ValueError("semantic_content 不能为空字符串")
        self._semantic_content = value

    def copy(self, **kwargs) -> "Axes":
        new_obj = super().copy(**kwargs)
        new_obj._semantic_type = self._semantic_type
        new_obj._semantic_role = self._semantic_role
        new_obj._semantic_content = self._semantic_content
        if hasattr(self, "_bbox_cache") and self._bbox_cache is not None:
            new_obj._bbox_cache = tuple(point.copy() for point in self._bbox_cache)
        else:
            new_obj._bbox_cache = None
        new_obj._bbox_signature = self._bbox_signature
        return new_obj

    def _normalize_range(
        self,
        range_terms: Optional[Sequence[float]],
        default: Sequence[float]
    ) -> Tuple[float, float, float]:
        if range_terms is None:
            values = list(default)
        else:
            values = list(range_terms)
        if len(values) == 2:
            values.append(1.0)
        if len(values) != 3:
            raise ValueError("坐标范围必须是长度为 2 或 3 的序列")
        start, end, step = map(float, values)
        if step == 0:
            raise ValueError("坐标步长不能为 0")
        if end == start:
            raise ValueError("坐标范围起点和终点不能相同")
        return start, end, step

    def _resolve_axis_length(
        self,
        range_terms: Sequence[float],
        explicit_length: Optional[float],
        unit_size: Optional[float]
    ) -> float:
        span = abs(float(range_terms[1]) - float(range_terms[0]))
        if unit_size is not None:
            length = span * float(unit_size)
        elif explicit_length is not None:
            length = float(explicit_length)
        else:
            length = span
        if length <= 0:
            raise ValueError("坐标轴长度必须为正数")
        return length

    def _invalidate_bbox_cache(self) -> None:
        self._bbox_cache = None
        self._bbox_signature = None

    def _compute_bbox_signature(self) -> Tuple[float, ...]:
        return tuple(np.round(self.get_points_defining_boundary().reshape(-1), 8))

    def create_axis(
        self,
        range_terms: Sequence[float],
        axis_config: Optional[dict] = None,
        length: Optional[float] = None
    ) -> NumberLine:
        config = {} if axis_config is None else dict(axis_config)
        
        # 【防线 1】：强行把 config 里可能潜伏的 length 剔除，防止解包时炸膛
        config.pop("length", None)
        
        axis_length = length
        if axis_length is None:
            # 兼容 AI 写的解析逻辑
            axis_length = self._resolve_axis_length(range_terms, None, getattr(self, "unit_size", None))
            
        axis = NumberLine(
            x_range=list(range_terms),
            **config
        )
        
        # 【防线 2】：ManimGL 的标准做法，实例化后强制设定物理宽度
        if axis_length is not None:
            axis.set_width(axis_length)
            
        return axis

    def coords_to_point(
        self,
        *coords: Union[float, np.ndarray, Sequence[float]]
    ) -> Union[np.ndarray, Sequence[np.ndarray]]:
        if len(coords) == 1 and isinstance(coords[0], (list, tuple, np.ndarray)):
            first = coords[0]
            if len(first) == 0:
                raise ValueError("坐标不能为空")
            if isinstance(first[0], (list, tuple, np.ndarray)):
                return [self.coords_to_point(*item) for item in first]
        if len(coords) < 2:
            raise ValueError("二维坐标至少需要提供 x 和 y")
        x = float(coords[0])
        y = float(coords[1])
        x_origin = self.x_axis.n2p(0)
        x_point = self.x_axis.n2p(x)
        y_point = self.y_axis.n2p(y)
        return x_point + (y_point - x_origin)

    def point_to_coords(self, point) -> Tuple[float, float]:
        point = np.array(point, dtype=float)
        x = float(self.x_axis.p2n(point))
        y = float(self.y_axis.p2n(point))
        return x, y

    def get_axes(self) -> VGroup:
        return self.axes

    def get_all_ranges(self) -> list[Sequence[float]]:
        return [self.x_range, self.y_range]

    def add_coordinate_labels(
        self,
        x_values: Optional[Iterable[float]] = None,
        y_values: Optional[Iterable[float]] = None,
        excluding: Optional[Iterable[float]] = None,
        **number_config
    ) -> VGroup:
        excluding_set = set() if excluding is None else {float(v) for v in excluding}
        x_vals = self._default_tick_values(self.x_range) if x_values is None else list(x_values)
        y_vals = self._default_tick_values(self.y_range) if y_values is None else list(y_values)

        labels = VGroup()

        for value in x_vals:
            numeric_value = float(value)
            if numeric_value in excluding_set:
                continue
            label = self.x_axis.get_number_mobject(numeric_value, **number_config)
            label.next_to(self.x_axis.n2p(numeric_value), DOWN, buff=0.1)
            labels.add(label)

        for value in y_vals:
            numeric_value = float(value)
            if numeric_value in excluding_set:
                continue
            label = self.y_axis.get_number_mobject(numeric_value, **number_config)
            label.next_to(self.y_axis.n2p(numeric_value), LEFT, buff=0.1)
            labels.add(label)

        if len(self.coordinate_labels) > 0:
            self.remove(self.coordinate_labels)
        self.coordinate_labels = labels
        self.add(self.coordinate_labels)
        self._invalidate_bbox_cache()
        return labels

    def _default_tick_values(self, range_terms: Sequence[float]) -> list[float]:
        start, end, step = map(float, range_terms)
        count = int(np.floor((end - start) / step)) + 1
        values = [start + index * step for index in range(count)]
        if values and values[-1] > end + 1e-8:
            values.pop()
        return values

    def get_bbox(self) -> Tuple[np.ndarray, np.ndarray]:
        # 为数据集安全性提供稳定包围盒：仅在几何结构变化时刷新缓存，避免重复调用波动
        signature = self._compute_bbox_signature()
        if self._bbox_cache is None or self._bbox_signature != signature:
            points = self.get_points_defining_boundary()
            if len(points) == 0:
                min_point = np.zeros(3)
                max_point = np.zeros(3)
            else:
                min_point = np.min(points, axis=0)
                max_point = np.max(points, axis=0)
            self._bbox_cache = (min_point.copy(), max_point.copy())
            self._bbox_signature = signature
        return self._bbox_cache[0].copy(), self._bbox_cache[1].copy()


def KinematicsAxes(
    x_range: Optional[Sequence[float]] = None,
    y_range: Optional[Sequence[float]] = None,
    **kwargs
) -> Axes:
    return Axes(
        x_range=x_range,
        y_range=y_range,
        semantic_type="coordinate_system",
        semantic_role="kinematics_coordinate",
        semantic_content="kinematics axes",
        **kwargs
    )


def StandardMathAxes(
    x_range: Optional[Sequence[float]] = None,
    y_range: Optional[Sequence[float]] = None,
    **kwargs
) -> Axes:
    return Axes(
        x_range=x_range,
        y_range=y_range,
        semantic_type="coordinate_system",
        semantic_role="standard_axes",
        semantic_content="x-y axes",
        **kwargs
    )


def ForceDiagramAxes(
    x_range: Optional[Sequence[float]] = None,
    y_range: Optional[Sequence[float]] = None,
    **kwargs
) -> Axes:
    return Axes(
        x_range=x_range,
        y_range=y_range,
        semantic_type="coordinate_system",
        semantic_role="force_diagram_coordinate",
        semantic_content="force diagram axes",
        **kwargs
    )