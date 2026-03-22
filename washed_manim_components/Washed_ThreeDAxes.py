from manimlib import *


class SemanticMixin:
    def _init_semantic_fields(
        self,
        semantic_type="",
        semantic_role="",
        semantic_content=None,
    ):
        self.semantic_type = semantic_type
        self.semantic_role = semantic_role
        self.semantic_content = semantic_content

    @property
    def semantic_type(self):
        return getattr(self, "_semantic_type", "")

    @semantic_type.setter
    def semantic_type(self, value):
        if not isinstance(value, str):
            raise TypeError("semantic_type must be a string")
        self._semantic_type = value

    @property
    def semantic_role(self):
        return getattr(self, "_semantic_role", "")

    @semantic_role.setter
    def semantic_role(self, value):
        if not isinstance(value, str):
            raise TypeError("semantic_role must be a string")
        self._semantic_role = value

    @property
    def semantic_content(self):
        return getattr(self, "_semantic_content", None)

    @semantic_content.setter
    def semantic_content(self, value):
        if value is not None and not isinstance(value, str):
            raise TypeError("semantic_content must be a string or None")
        self._semantic_content = value


class CleanThreeDAxes(Axes, SemanticMixin):
    def __init__(
        self,
        x_range=(-6, 6, 1),
        y_range=(-4, 4, 1),
        z_range=(-4, 4, 1),
        z_axis_config=None,
        z_normal=DOWN,
        depth=6,
        semantic_role="",
        semantic_content=None,
        **kwargs
    ):
        super().__init__(x_range=x_range, y_range=y_range, **kwargs)

        self._init_semantic_fields(
            semantic_type="coordinate_system",
            semantic_role=semantic_role,
            semantic_content=semantic_content,
        )

        self.z_range = self._normalize_range(z_range)
        self.z_normal = np.array(z_normal)
        self.depth = float(depth)
        self.z_axis_config = dict(z_axis_config or {})
        self.z_axis = self._create_z_axis()
        self.add(self.z_axis)

    def _normalize_range(self, value):
        if not isinstance(value, (list, tuple)):
            raise TypeError("range must be a list or tuple")
        if len(value) == 2:
            return (value[0], value[1], 1)
        if len(value) == 3:
            return (value[0], value[1], value[2])
        raise ValueError("range must have length 2 or 3")

    def _create_z_axis(self):
        z_min, z_max, z_step = self.z_range
        axis_config = dict(self.axis_config)
        axis_config.update(self.z_axis_config)
        z_axis = NumberLine(
            x_range=(z_min, z_max, z_step),
            **axis_config
        )
        z_axis.set_height(self.depth)
        z_axis.rotate(PI / 2, RIGHT, about_point=ORIGIN)
        if np.linalg.norm(self.z_normal) > 0:
            reference = OUT
            target = normalize(self.z_normal)
            if np.linalg.norm(np.cross(reference, target)) > 1e-8:
                z_axis.rotate(
                    angle_between_vectors(reference, target),
                    axis=normalize(np.cross(reference, target)),
                    about_point=ORIGIN,
                )
            elif np.dot(reference, target) < 0:
                z_axis.rotate(PI, RIGHT, about_point=ORIGIN)
        z_axis.shift(self.get_origin() - z_axis.n2p(0))
        return z_axis

    def get_all_ranges(self):
        return [self.x_range, self.y_range, self.z_range]

    def add_axis_labels(
        self,
        x_tex="x",
        y_tex="y",
        z_tex="z",
        font_size=36,
        buff=SMALL_BUFF,
    ):
        x_label = Tex(x_tex, font_size=font_size)
        y_label = Tex(y_tex, font_size=font_size)
        z_label = Tex(z_tex, font_size=font_size)

        x_label.next_to(self.x_axis.get_end(), RIGHT, buff=buff)
        y_label.next_to(self.y_axis.get_end(), UP, buff=buff)
        z_label.next_to(self.z_axis.get_end(), normalize(self.z_normal), buff=buff)

        x_label.semantic_type = "math_formula"
        x_label.semantic_role = "x_axis_label"
        x_label.semantic_content = x_tex

        y_label.semantic_type = "math_formula"
        y_label.semantic_role = "y_axis_label"
        y_label.semantic_content = y_tex

        z_label.semantic_type = "math_formula"
        z_label.semantic_role = "z_axis_label"
        z_label.semantic_content = z_tex

        self.axis_labels = VGroup(x_label, y_label, z_label)
        self.add(self.axis_labels)
        return self.axis_labels

    def coords_to_point(self, x, y, z=0):
        base_point = super().coords_to_point(x, y)
        z_offset = self.z_axis.n2p(z) - self.z_axis.n2p(0)
        return base_point + z_offset

    def c2p(self, x, y, z=0):
        return self.coords_to_point(x, y, z)

    def point_to_coords(self, point):
        x, y = super().point_to_coords(point)
        z_vector = self.z_axis.get_end() - self.z_axis.get_start()
        z_norm_sq = np.dot(z_vector, z_vector)
        if z_norm_sq < 1e-8:
            z = 0
        else:
            z0 = self.z_axis.n2p(0)
            z_scale = self.z_range[1] - self.z_range[0]
            if abs(z_scale) < 1e-8:
                z = self.z_range[0]
            else:
                line_length_sq = np.dot(self.z_axis.n2p(self.z_range[1]) - z0, self.z_axis.n2p(self.z_range[1]) - z0)
                if line_length_sq < 1e-8:
                    z = 0
                else:
                    projection = np.dot(point - z0, self.z_axis.n2p(self.z_range[1]) - z0) / line_length_sq
                    z = self.z_range[0] + projection * (self.z_range[1] - self.z_range[0])
        return np.array([x, y, z])

    def p2c(self, point):
        return self.point_to_coords(point)

    def get_graph(
        self,
        func,
        color=BLUE,
        opacity=1.0,
        u_range=None,
        v_range=None,
        **kwargs
    ):
        if u_range is None:
            u_range = self.x_range[:2]
        if v_range is None:
            v_range = self.y_range[:2]

        surface = ParametricSurface(
            lambda u, v: self.c2p(u, v, func(u, v)),
            u_range=u_range,
            v_range=v_range,
            color=color,
            opacity=opacity,
            **kwargs
        )
        surface.semantic_type = "function_curve"
        surface.semantic_role = "surface_graph"
        surface.semantic_content = getattr(func, "__name__", None)
        return surface

    def get_parametric_surface(
        self,
        func,
        color=BLUE,
        opacity=1.0,
        u_range=None,
        v_range=None,
        **kwargs
    ):
        if u_range is None:
            u_range = (0, 1)
        if v_range is None:
            v_range = (0, 1)

        surface = ParametricSurface(
            lambda u, v: self.c2p(*func(u, v)),
            u_range=u_range,
            v_range=v_range,
            color=color,
            opacity=opacity,
            **kwargs
        )
        surface.semantic_type = "function_curve"
        surface.semantic_role = "parametric_surface"
        surface.semantic_content = getattr(func, "__name__", None)
        return surface

    def get_bbox(self):
        return np.array(self.get_bounding_box())

    def copy(self, **kwargs):
        new_obj = super().copy(**kwargs)
        new_obj._semantic_type = getattr(self, "_semantic_type", "")
        new_obj._semantic_role = getattr(self, "_semantic_role", "")
        new_obj._semantic_content = getattr(self, "_semantic_content", None)
        return new_obj


class SemanticTex(Tex, SemanticMixin):
    def __init__(
        self,
        *tex_strings,
        semantic_type="math_formula",
        semantic_role="",
        semantic_content=None,
        **kwargs
    ):
        super().__init__(*tex_strings, **kwargs)
        if semantic_content is None:
            semantic_content = "".join(str(s) for s in tex_strings)
        self._init_semantic_fields(
            semantic_type=semantic_type,
            semantic_role=semantic_role,
            semantic_content=semantic_content,
        )

    def copy(self, **kwargs):
        new_obj = super().copy(**kwargs)
        new_obj._semantic_type = getattr(self, "_semantic_type", "")
        new_obj._semantic_role = getattr(self, "_semantic_role", "")
        new_obj._semantic_content = getattr(self, "_semantic_content", None)
        return new_obj


class SemanticParametricSurface(ParametricSurface, SemanticMixin):
    def __init__(
        self,
        func,
        semantic_type="function_curve",
        semantic_role="",
        semantic_content=None,
        **kwargs
    ):
        super().__init__(func, **kwargs)
        self._init_semantic_fields(
            semantic_type=semantic_type,
            semantic_role=semantic_role,
            semantic_content=semantic_content,
        )

    def copy(self, **kwargs):
        new_obj = super().copy(**kwargs)
        new_obj._semantic_type = getattr(self, "_semantic_type", "")
        new_obj._semantic_role = getattr(self, "_semantic_role", "")
        new_obj._semantic_content = getattr(self, "_semantic_content", None)
        return new_obj


def KinematicsThreeDAxes(
    x_range=(-6, 6, 1),
    y_range=(-4, 4, 1),
    z_range=(-4, 4, 1),
    **kwargs
):
    return CleanThreeDAxes(
        x_range=x_range,
        y_range=y_range,
        z_range=z_range,
        semantic_role="kinematics_coordinate",
        **kwargs
    )


def AnalyticGeometryThreeDAxes(
    x_range=(-5, 5, 1),
    y_range=(-5, 5, 1),
    z_range=(-5, 5, 1),
    **kwargs
):
    return CleanThreeDAxes(
        x_range=x_range,
        y_range=y_range,
        z_range=z_range,
        semantic_role="analytic_geometry_coordinate",
        **kwargs
    )


def PhysicsFieldThreeDAxes(
    x_range=(-4, 4, 1),
    y_range=(-4, 4, 1),
    z_range=(-4, 4, 1),
    **kwargs
):
    return CleanThreeDAxes(
        x_range=x_range,
        y_range=y_range,
        z_range=z_range,
        semantic_role="physics_3d_coordinate",
        **kwargs
    )