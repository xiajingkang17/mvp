from manimlib import *
import numpy as np


class SemanticMixin(object):
    def _init_semantics(self, semantic_type="", semantic_role="", semantic_content=None):
        self._semantic_type = ""
        self._semantic_role = ""
        self._semantic_content = None
        self.semantic_type = semantic_type
        self.semantic_role = semantic_role
        self.semantic_content = semantic_content

    @property
    def semantic_type(self):
        return self._semantic_type

    @semantic_type.setter
    def semantic_type(self, value):
        if not isinstance(value, str):
            raise TypeError("semantic_type must be a string")
        self._semantic_type = value

    @property
    def semantic_role(self):
        return self._semantic_role

    @semantic_role.setter
    def semantic_role(self, value):
        if not isinstance(value, str):
            raise TypeError("semantic_role must be a string")
        self._semantic_role = value

    @property
    def semantic_content(self):
        return self._semantic_content

    @semantic_content.setter
    def semantic_content(self, value):
        if value is not None and not isinstance(value, str):
            raise TypeError("semantic_content must be a string or None")
        self._semantic_content = value


class VectorField(VGroup, SemanticMixin):
    def __init__(
        self,
        func,
        coordinate_system=None,
        sample_coords=None,
        density=1.0,
        magnitude_range=(0.0, 2.0),
        color=BLUE,
        color_map_name="3b1b_colormap",
        color_map=None,
        stroke_opacity=1.0,
        stroke_width=3.0,
        tip_width_ratio=4.0,
        tip_len_to_width=1.5,
        max_vect_len=0.5,
        max_vect_len_to_step_size=0.9,
        flat_stroke=False,
        norm_to_opacity_func=None,
        semantic_type="vector_field",
        semantic_role="vector_field",
        semantic_content=None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self._init_semantics(
            semantic_type=semantic_type,
            semantic_role=semantic_role,
            semantic_content=semantic_content,
        )

        self.func = func
        self.coordinate_system = coordinate_system
        self.density = max(float(density), 1e-8)
        self.magnitude_range = magnitude_range if magnitude_range is not None else (0.0, 1.0)
        self.base_color = color
        self.color_map_name = color_map_name
        self.color_map = color_map
        self.stroke_opacity = stroke_opacity
        self.base_stroke_width = stroke_width
        self.tip_width_ratio = tip_width_ratio
        self.tip_len_to_width = tip_len_to_width
        self.max_vect_len = max_vect_len
        self.max_vect_len_to_step_size = max_vect_len_to_step_size
        self.flat_stroke = flat_stroke
        self.norm_to_opacity_func = norm_to_opacity_func

        self.sample_coords = np.zeros((0, 3))
        self.base_stroke_width_array = np.zeros(0)
        self.vectors = VGroup()
        self.add(self.vectors)

        if sample_coords is None:
            sample_coords = self.get_sample_points_from_coordinate_system()
        self.set_sample_coords(sample_coords)

    def copy(self, **kwargs):
        new_obj = super().copy(**kwargs)
        new_obj._semantic_type = getattr(self, "_semantic_type", "")
        new_obj._semantic_role = getattr(self, "_semantic_role", "")
        new_obj._semantic_content = getattr(self, "_semantic_content", None)
        return new_obj

    def init_points(self):
        self.update_vectors()
        return self

    def get_sample_points(self, center, width, height, depth=0.0, x_density=1.0, y_density=1.0, z_density=1.0):
        center = np.array(center, dtype=float)
        x_step = 1.0 / max(float(x_density), 1e-8)
        y_step = 1.0 / max(float(y_density), 1e-8)
        z_step = 1.0 / max(float(z_density), 1e-8)

        x_values = self._get_axis_values(center[0], width, x_step)
        y_values = self._get_axis_values(center[1], height, y_step)

        if depth <= 0:
            z_values = np.array([center[2]])
        else:
            z_values = self._get_axis_values(center[2], depth, z_step)

        grid = np.array(
            [[x, y, z] for z in z_values for y in y_values for x in x_values],
            dtype=float
        )
        return grid

    def init_base_stroke_width_array(self, n_sample_points):
        width = float(self.base_stroke_width)
        self.base_stroke_width_array = np.full(int(n_sample_points), width)
        return self.base_stroke_width_array

    def set_sample_coords(self, sample_coords):
        coords = np.array(sample_coords, dtype=float)
        if coords.ndim != 2 or coords.shape[1] != 3:
            raise ValueError("sample_coords must be an array of shape (n, 3)")
        self.sample_coords = coords.copy()
        self.init_base_stroke_width_array(len(self.sample_coords))
        self.update_vectors()
        return self

    def set_stroke(
        self,
        color=None,
        width=None,
        opacity=None,
        behind=None,
        flat=None,
        recurse=True
    ):
        if color is not None:
            self.base_color = color
        if width is not None:
            self.base_stroke_width = width
        if opacity is not None:
            self.stroke_opacity = opacity
        if flat is not None:
            self.flat_stroke = flat
        self.update_vectors()
        return self

    def set_stroke_width(self, width):
        self.base_stroke_width = width
        self.update_vectors()
        return self

    def update_sample_points(self):
        if self.coordinate_system is not None:
            self.sample_coords = self.get_sample_points_from_coordinate_system()
            self.init_base_stroke_width_array(len(self.sample_coords))
            self.update_vectors()
        return self

    def update_vectors(self):
        new_vectors = VGroup()
        for point, width in zip(self.sample_coords, self.base_stroke_width_array):
            vector = self._vector_from_point(point, width)
            if vector is not None:
                new_vectors.add(vector)

        if len(self.submobjects) == 0:
            self.add(new_vectors)
        elif len(self.submobjects) == 1 and self.submobjects[0] is self.vectors:
            self.submobjects[0] = new_vectors
        else:
            self.submobjects = [new_vectors]
        self.vectors = new_vectors
        self.refresh_bounding_box()
        return self

    def get_sample_points_from_coordinate_system(self):
        cs = self.coordinate_system
        if cs is None:
            return self.get_sample_points(ORIGIN, 8.0, 8.0, 0.0, self.density, self.density, 1.0)

        x_range = self._extract_range(getattr(cs, "x_range", None), -4.0, 4.0)
        y_range = self._extract_range(getattr(cs, "y_range", None), -3.0, 3.0)
        z_attr = getattr(cs, "z_range", None)
        z_range = self._extract_range(z_attr, 0.0, 0.0) if z_attr is not None else (0.0, 0.0)

        x_values = self._get_range_values(x_range, self.density)
        y_values = self._get_range_values(y_range, self.density)
        z_values = self._get_range_values(z_range, self.density) if abs(z_range[1] - z_range[0]) > 1e-8 else np.array([0.0])

        points = []
        for z in z_values:
            for y in y_values:
                for x in x_values:
                    if hasattr(cs, "c2p"):
                        points.append(np.array(cs.c2p(x, y, z), dtype=float))
                    else:
                        points.append(np.array([x, y, z], dtype=float))
        return np.array(points, dtype=float)

    def _vector_from_point(self, point, stroke_width):
        value = np.array(self.func(np.array(point, dtype=float)), dtype=float).reshape(-1)
        if value.size == 2:
            value = np.array([value[0], value[1], 0.0])
        if value.size != 3 or not np.all(np.isfinite(value)):
            return None

        norm = get_norm(value)
        if norm < 1e-8:
            return None

        length = self._get_vector_length(norm)
        direction = value / norm
        start = np.array(point, dtype=float)
        end = start + direction * length

        vector = Arrow(
            start,
            end,
            buff=0,
            stroke_width=float(stroke_width),
            tip_width_ratio=self.tip_width_ratio,
            tip_len_to_width=self.tip_len_to_width,
        )
        vector.set_stroke(
            color=self._get_vector_color(norm),
            width=float(stroke_width),
            opacity=self._get_vector_opacity(norm),
        )
        if hasattr(vector, "set_flat_stroke"):
            vector.set_flat_stroke(self.flat_stroke)
        return vector

    def _get_vector_length(self, norm):
        if len(self.sample_coords) > 1:
            step_size = self._estimate_step_size()
            cap = min(float(self.max_vect_len), float(self.max_vect_len_to_step_size) * step_size)
        else:
            cap = float(self.max_vect_len)
        if cap <= 0:
            return 0.0
        return cap * np.tanh(norm)

    def _estimate_step_size(self):
        if len(self.sample_coords) < 2:
            return 1.0
        diffs = self.sample_coords[1:] - self.sample_coords[:-1]
        norms = np.array([get_norm(diff) for diff in diffs if get_norm(diff) > 1e-8], dtype=float)
        if len(norms) == 0:
            return 1.0
        return float(np.min(norms))

    def _get_vector_color(self, norm):
        if callable(self.color_map):
            return self.color_map(norm)

        min_mag, max_mag = self._sanitize_magnitude_range()
        alpha = inverse_interpolate(min_mag, max_mag, np.clip(norm, min_mag, max_mag))
        if self.color_map is not None and isinstance(self.color_map, (list, tuple)) and len(self.color_map) > 0:
            return interpolate_color(self.color_map[0], self.color_map[-1], alpha)
        return interpolate_color(BLUE_E, YELLOW, alpha)

    def _get_vector_opacity(self, norm):
        if callable(self.norm_to_opacity_func):
            opacity = self.norm_to_opacity_func(norm)
            return float(np.clip(opacity, 0.0, 1.0))
        return float(np.clip(self.stroke_opacity, 0.0, 1.0))

    def _sanitize_magnitude_range(self):
        if self.magnitude_range is None or len(self.magnitude_range) != 2:
            return (0.0, 1.0)
        low = float(self.magnitude_range[0])
        high = float(self.magnitude_range[1])
        if high <= low:
            high = low + 1.0
        return (low, high)

    def _extract_range(self, value, default_min, default_max):
        if value is None:
            return (float(default_min), float(default_max))
        if len(value) >= 2:
            return (float(value[0]), float(value[1]))
        return (float(default_min), float(default_max))

    def _get_range_values(self, value_range, density):
        start, end = value_range
        if abs(end - start) < 1e-8:
            return np.array([start])
        step = 1.0 / max(float(density), 1e-8)
        count = max(int(np.floor((end - start) / step + 1e-8)) + 1, 2)
        return np.linspace(start, end, count)

    def _get_axis_values(self, center, span, step):
        if span <= 0:
            return np.array([center])
        start = center - span / 2.0
        end = center + span / 2.0
        count = max(int(np.floor(span / step + 1e-8)) + 1, 2)
        return np.linspace(start, end, count)


def KinematicsVectorField(func, coordinate_system=None, semantic_content=None, **kwargs):
    return VectorField(
        func=func,
        coordinate_system=coordinate_system,
        semantic_type="vector_field",
        semantic_role="kinematics_vector_field",
        semantic_content=semantic_content,
        **kwargs
    )


def ElectricField(func, coordinate_system=None, semantic_content=None, **kwargs):
    return VectorField(
        func=func,
        coordinate_system=coordinate_system,
        semantic_type="vector_field",
        semantic_role="electric_field_line",
        semantic_content=semantic_content,
        **kwargs
    )


def GravitationalField(func, coordinate_system=None, semantic_content=None, **kwargs):
    return VectorField(
        func=func,
        coordinate_system=coordinate_system,
        semantic_type="vector_field",
        semantic_role="gravitational_field",
        semantic_content=semantic_content,
        **kwargs
    )