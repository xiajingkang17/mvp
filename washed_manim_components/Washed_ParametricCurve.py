from manimlib import *
import numpy as np


class ParametricCurve(VMobject):
    def __init__(
        self,
        t_func,
        t_range=None,
        epsilon=1e-8,
        discontinuities=None,
        use_smoothing=True,
        semantic_type="function_curve",
        semantic_role="parametric_curve",
        semantic_content=None,
        **kwargs
    ):
        self.t_func = t_func
        self.t_range = self._normalize_t_range(t_range)
        self.epsilon = float(epsilon)
        self.discontinuities = list(discontinuities) if discontinuities is not None else []
        self.use_smoothing = bool(use_smoothing)

        self._semantic_type = ""
        self._semantic_role = ""
        self._semantic_content = None

        super().__init__(**kwargs)

        self.semantic_type = semantic_type
        self.semantic_role = semantic_role
        self.semantic_content = semantic_content

        self.init_points()

    @staticmethod
    def _normalize_t_range(t_range):
        if t_range is None:
            return np.array([0.0, 1.0, 0.1], dtype=float)
        if len(t_range) == 2:
            return np.array([t_range[0], t_range[1], 0.1], dtype=float)
        if len(t_range) == 3:
            return np.array(t_range, dtype=float)
        raise ValueError("t_range must have length 2 or 3")

    @property
    def semantic_type(self):
        return self._semantic_type

    @semantic_type.setter
    def semantic_type(self, value):
        if not isinstance(value, str):
            raise TypeError("semantic_type must be a string")
        if not value.strip():
            raise ValueError("semantic_type must be a non-empty string")
        self._semantic_type = value

    @property
    def semantic_role(self):
        return self._semantic_role

    @semantic_role.setter
    def semantic_role(self, value):
        if not isinstance(value, str):
            raise TypeError("semantic_role must be a string")
        if not value.strip():
            raise ValueError("semantic_role must be a non-empty string")
        self._semantic_role = value

    @property
    def semantic_content(self):
        return self._semantic_content

    @semantic_content.setter
    def semantic_content(self, value):
        if value is not None and not isinstance(value, str):
            raise TypeError("semantic_content must be a string or None")
        self._semantic_content = value

    def copy(self, **kwargs):
        new_obj = super().copy(**kwargs)
        new_obj._semantic_type = getattr(self, "_semantic_type", "")
        new_obj._semantic_role = getattr(self, "_semantic_role", "")
        new_obj._semantic_content = getattr(self, "_semantic_content", None)
        return new_obj

    def get_point_from_function(self, t):
        point = self.t_func(t)
        point = np.array(point, dtype=float)
        if point.ndim != 1:
            raise ValueError("t_func must return a 1D point-like value")
        if len(point) == 2:
            point = np.append(point, 0.0)
        elif len(point) != 3:
            raise ValueError("t_func must return a 2D or 3D point")
        return point

    def _get_clean_discontinuities(self):
        t_min, t_max = self.t_range[:2]
        return sorted(
            float(t)
            for t in self.discontinuities
            if t_min < float(t) < t_max
        )

    def _get_subranges(self):
        t_min, t_max, _step = self.t_range
        boundaries = [t_min]
        for t in self._get_clean_discontinuities():
            boundaries.extend([t - self.epsilon, t + self.epsilon])
        boundaries.append(t_max)

        subranges = []
        for start, end in zip(boundaries[0::2], boundaries[1::2]):
            if end > start:
                subranges.append((start, end))
        return subranges

    def _get_sample_times(self, t_start, t_end):
        step = abs(self.t_range[2])
        if step <= 0:
            raise ValueError("t_range step must be positive")
        count = max(int(np.ceil((t_end - t_start) / step)), 1)
        times = np.linspace(t_start, t_end, count + 1)
        if len(times) < 2:
            times = np.array([t_start, t_end], dtype=float)
        return times

    def init_points(self):
        self.clear_points()
        for t_start, t_end in self._get_subranges():
            times = self._get_sample_times(t_start, t_end)
            points = np.array([self.get_point_from_function(t) for t in times])
            if len(points) == 0:
                continue
            self.start_new_path(points[0])
            if len(points) > 1:
                self.add_points_as_corners(points[1:])
        if self.use_smoothing and self.has_points():
            self.make_approximately_smooth()
        return self

    def get_t_func(self):
        return self.t_func

    def get_function(self):
        return self.t_func

    def get_x_range(self):
        return np.array(self.t_range, dtype=float)

    def set_semantic_labels(self, semantic_type=None, semantic_role=None, semantic_content=None):
        if semantic_type is not None:
            self.semantic_type = semantic_type
        if semantic_role is not None:
            self.semantic_role = semantic_role
        if semantic_content is not None or semantic_content is None:
            self.semantic_content = semantic_content
        return self

    def get_bbox(self):
        return np.array(self.get_bounding_box(), copy=True)


def KinematicsParametricCurve(t_func, t_range=None, semantic_content=None, **kwargs):
    return ParametricCurve(
        t_func=t_func,
        t_range=t_range,
        semantic_type="function_curve",
        semantic_role="kinematics_curve",
        semantic_content=semantic_content,
        **kwargs
    )


def ProjectileTrajectoryCurve(t_func, t_range=None, semantic_content=None, **kwargs):
    return ParametricCurve(
        t_func=t_func,
        t_range=t_range,
        semantic_type="function_curve",
        semantic_role="projectile_trajectory",
        semantic_content=semantic_content,
        **kwargs
    )


def UnitCircleParametricCurve(t_range=None, **kwargs):
    if t_range is None:
        t_range = [0.0, TAU, 0.05]
    return ParametricCurve(
        t_func=lambda t: np.array([np.cos(t), np.sin(t), 0.0]),
        t_range=t_range,
        semantic_type="function_curve",
        semantic_role="unit_circle_parameterization",
        semantic_content="(cos(t), sin(t))",
        **kwargs
    )