from manimlib import *


class NumberPlane(Axes):
    def __init__(
        self,
        x_range=None,
        y_range=None,
        background_line_style=None,
        faded_line_style=None,
        faded_line_ratio=4,
        make_smooth_after_applying_functions=True,
        semantic_type="coordinate_system",
        semantic_role="coordinate_plane",
        semantic_content=None,
        **kwargs
    ):
        if x_range is None:
            x_range = (-8, 8, 1)
        if y_range is None:
            y_range = (-4, 4, 1)

        self.background_line_style = dict(
            stroke_color=BLUE_E,
            stroke_width=1,
            stroke_opacity=0.8,
        )
        if background_line_style is not None:
            self.background_line_style.update(background_line_style)

        self.faded_line_style = dict(
            stroke_color=self.background_line_style.get("stroke_color", BLUE_E),
            stroke_width=max(self.background_line_style.get("stroke_width", 1) * 0.5, 0.5),
            stroke_opacity=max(self.background_line_style.get("stroke_opacity", 0.8) * 0.5, 0.1),
        )
        if faded_line_style is not None:
            self.faded_line_style.update(faded_line_style)

        self.faded_line_ratio = max(1, int(faded_line_ratio))
        self.make_smooth_after_applying_functions = bool(make_smooth_after_applying_functions)

        super().__init__(x_range=x_range, y_range=y_range, **kwargs)

        self._semantic_type = ""
        self._semantic_role = ""
        self._semantic_content = None
        self.semantic_type = semantic_type
        self.semantic_role = semantic_role
        self.semantic_content = semantic_content

        self.background_lines = VGroup()
        self.faded_lines = VGroup()
        self.init_background_lines()
        self.add_to_back(self.faded_lines, self.background_lines)

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

    def init_background_lines(self):
        self.background_lines, self.faded_lines = self.get_lines()
        return self

    def get_lines(self):
        x_axis, y_axis = self.get_axes()
        horiz_main, horiz_faded = self.get_lines_parallel_to_axis(x_axis, y_axis)
        vert_main, vert_faded = self.get_lines_parallel_to_axis(y_axis, x_axis)
        return (
            VGroup(*horiz_main, *vert_main),
            VGroup(*horiz_faded, *vert_faded),
        )

    def get_lines_parallel_to_axis(self, axis1, axis2):
        freq = self.faded_line_ratio + 1
        step = axis2.x_step if hasattr(axis2, "x_step") else 1
        if step == 0:
            step = 1

        axis_min = axis2.x_min if hasattr(axis2, "x_min") else -1
        axis_max = axis2.x_max if hasattr(axis2, "x_max") else 1

        line = Line(axis1.get_start(), axis1.get_end())
        main_lines = VGroup()
        faded_lines = VGroup()

        center_value = axis2.n2p(0)[0 if abs(axis2.get_end()[0] - axis2.get_start()[0]) > abs(axis2.get_end()[1] - axis2.get_start()[1]) else 1]

        values = np.arange(axis_min, axis_max + step * 0.5, step)
        for value in values:
            if abs(value) < 1e-8:
                continue
            target_point = axis2.n2p(value)
            shift_vect = target_point - axis2.n2p(0)
            new_line = line.copy()
            new_line.shift(shift_vect)
            if int(round(value / step)) % freq == 0:
                new_line.set_style(**self.background_line_style)
                main_lines.add(new_line)
            else:
                new_line.set_style(**self.faded_line_style)
                faded_lines.add(new_line)

        return main_lines, faded_lines

    def get_x_unit_size(self):
        x_axis = self.get_x_axis()
        return x_axis.get_unit_size()

    def get_y_unit_size(self):
        y_axis = self.get_y_axis()
        return y_axis.get_unit_size()

    def get_axes(self):
        return VGroup(self.get_x_axis(), self.get_y_axis())

    def get_vector(self, coords):
        end_point = self.c2p(*coords)
        vector = Arrow(self.get_origin(), end_point, buff=0)
        vector.semantic_type = "geometric_shape" if hasattr(vector, "semantic_type") else None
        return vector

    def prepare_for_nonlinear_transform(self, num_inserted_curves=50):
        for mob in self.family_members_with_points():
            mob.insert_n_curves(num_inserted_curves)
            if self.make_smooth_after_applying_functions and hasattr(mob, "make_smooth"):
                mob.make_smooth()
        return self


def KinematicsPlane(**kwargs):
    return NumberPlane(
        semantic_type="coordinate_system",
        semantic_role="kinematics_coordinate",
        semantic_content="x-t or v-t plane",
        **kwargs
    )


def CartesianMathPlane(**kwargs):
    return NumberPlane(
        semantic_type="coordinate_system",
        semantic_role="cartesian_plane",
        semantic_content="x-y",
        **kwargs
    )


def ForceDiagramPlane(**kwargs):
    return NumberPlane(
        semantic_type="coordinate_system",
        semantic_role="force_analysis_plane",
        semantic_content="Fx-Fy",
        **kwargs
    )