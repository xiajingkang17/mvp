from manimlib import *
import numpy as np


class StreamLines(VGroup):
    def __init__(
        self,
        func,
        coordinate_system,
        density=1.0,
        n_repeats=1,
        noise_factor=None,
        solution_time=3.0,
        dt=0.05,
        arc_len=3.0,
        max_time_steps=200,
        n_samples_per_line=20,
        cutoff_norm=15.0,
        stroke_width=2.0,
        stroke_color=BLUE,
        stroke_opacity=1.0,
        color_by_magnitude=False,
        magnitude_range=(0.0, 2.0),
        taper_stroke_width=False,
        color_map="3b1b_colormap",
        semantic_type="vector_field",
        semantic_role="stream_line_field",
        semantic_content=None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.func = func
        self.coordinate_system = coordinate_system
        self.density = density
        self.n_repeats = max(1, int(n_repeats))
        self.noise_factor = noise_factor
        self.solution_time = float(solution_time)
        self.dt = float(dt)
        self.arc_len = float(arc_len)
        self.max_time_steps = max(1, int(max_time_steps))
        self.n_samples_per_line = max(2, int(n_samples_per_line))
        self.cutoff_norm = float(cutoff_norm)
        self.stroke_width = float(stroke_width)
        self.stroke_color = stroke_color
        self.stroke_opacity = float(stroke_opacity)
        self.color_by_magnitude = bool(color_by_magnitude)
        self.magnitude_range = magnitude_range
        self.taper_stroke_width = bool(taper_stroke_width)
        self.color_map = color_map

        self._semantic_type = ""
        self._semantic_role = ""
        self._semantic_content = None
        self.semantic_type = semantic_type
        self.semantic_role = semantic_role
        self.semantic_content = semantic_content

        self._sample_coords_cache = None
        self._line_data_cache = None

        self.draw_lines()
        self.init_style()

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

    def point_func(self, points):
        points = np.array(points)
        single_point = points.ndim == 1
        if single_point:
            points = points.reshape(1, -1)

        vectors = []
        for point in points:
            coords = self.coordinate_system.p2c(point)
            value = np.array(self.func(*coords), dtype=float)
            if value.ndim == 0:
                value = np.array([value, 0.0, 0.0])
            if len(value) == 2:
                value = np.array([value[0], value[1], 0.0])
            elif len(value) < 2:
                value = np.array([0.0, 0.0, 0.0])
            vectors.append(value[:3])

        vectors = np.array(vectors)
        if single_point:
            return vectors[0]
        return vectors

    def draw_lines(self):
        self.clear()
        line_data = []

        for start_point in self.get_sample_coords():
            for repeat_index in range(self.n_repeats):
                seed_point = np.array(start_point, dtype=float)
                if self.noise_factor not in (None, 0):
                    seed_point = seed_point + self.noise_factor * np.random.normal(size=3)
                    seed_point[2] = start_point[2]

                points = self._integrate_from_point(seed_point)
                if len(points) < 2:
                    continue

                line = VMobject()
                line.set_points_smoothly(points)
                line_data.append((line, points, repeat_index))

        self._line_data_cache = line_data

        for line, _, _ in line_data:
            self.add(line)

    def get_sample_coords(self):
        if self._sample_coords_cache is not None:
            return [point.copy() for point in self._sample_coords_cache]

        cs = self.coordinate_system
        x_axis = getattr(cs, "x_axis", None)
        y_axis = getattr(cs, "y_axis", None)

        if x_axis is None or y_axis is None:
            raise ValueError("coordinate_system must provide x_axis and y_axis")

        x_min = x_axis.x_min
        x_max = x_axis.x_max
        y_min = y_axis.x_min
        y_max = y_axis.x_max

        x_step = self._get_axis_step(x_axis, self.density)
        y_step = self._get_axis_step(y_axis, self.density)

        x_values = self._inclusive_arange(x_min, x_max, x_step)
        y_values = self._inclusive_arange(y_min, y_max, y_step)

        sample_points = [
            np.array(cs.c2p(x, y), dtype=float)
            for y in y_values
            for x in x_values
        ]
        self._sample_coords_cache = [point.copy() for point in sample_points]
        return sample_points

    def init_style(self):
        min_mag, max_mag = self.magnitude_range
        span = max(max_mag - min_mag, 1e-8)

        for line, points, _ in (self._line_data_cache or []):
            line.set_stroke(
                color=self.stroke_color,
                width=self.stroke_width,
                opacity=self.stroke_opacity,
            )

            if self.taper_stroke_width:
                line.set_stroke(width=[0, self.stroke_width, 0])

            if self.color_by_magnitude and len(points) > 0:
                vectors = self.point_func(points)
                magnitudes = np.linalg.norm(vectors, axis=1)
                avg_magnitude = float(np.mean(magnitudes))
                alpha = np.clip((avg_magnitude - min_mag) / span, 0.0, 1.0)
                line.set_color(interpolate_color(BLUE_E, YELLOW, alpha))

    def _integrate_from_point(self, start_point):
        total_time = min(self.solution_time, self.max_time_steps * self.dt)
        n_steps = max(2, int(np.ceil(total_time / self.dt)))
        points = [np.array(start_point, dtype=float)]
        traveled = 0.0

        for _ in range(n_steps - 1):
            current = points[-1]
            vector = np.array(self.point_func(current), dtype=float)
            norm = get_norm(vector)

            if norm < 1e-8 or norm > self.cutoff_norm:
                break

            step = vector * self.dt
            next_point = current + step
            step_size = get_norm(next_point - current)

            if step_size < 1e-8:
                break

            traveled += step_size
            points.append(next_point)

            if traveled >= self.arc_len:
                break

            if len(points) >= self.max_time_steps:
                break

        if len(points) > self.n_samples_per_line:
            indices = np.linspace(0, len(points) - 1, self.n_samples_per_line).astype(int)
            points = [points[index] for index in indices]

        return points

    def _get_axis_step(self, axis, density):
        unit_size = axis.get_unit_size()
        if unit_size <= 1e-8:
            return 1.0
        base_step = 1.0 / max(density, 1e-8)
        return base_step

    def _inclusive_arange(self, start, stop, step):
        if step <= 0:
            raise ValueError("step must be positive")
        values = list(np.arange(start, stop + 0.5 * step, step))
        if len(values) == 0:
            values = [start]
        return values

    def get_bbox(self):
        return self.get_bounding_box()


def KinematicsStreamLines(func, coordinate_system, semantic_content=None, **kwargs):
    return StreamLines(
        func=func,
        coordinate_system=coordinate_system,
        semantic_type="vector_field",
        semantic_role="kinematics_flow_field",
        semantic_content=semantic_content,
        **kwargs
    )


def ElectricFieldStreamLines(func, coordinate_system, semantic_content=None, **kwargs):
    return StreamLines(
        func=func,
        coordinate_system=coordinate_system,
        semantic_type="vector_field",
        semantic_role="electric_field_line",
        semantic_content=semantic_content,
        **kwargs
    )


def PhaseFlowStreamLines(func, coordinate_system, semantic_content=None, **kwargs):
    return StreamLines(
        func=func,
        coordinate_system=coordinate_system,
        semantic_type="vector_field",
        semantic_role="phase_flow",
        semantic_content=semantic_content,
        **kwargs
    )