from manimlib import *


class Arrow(Line):
    tickness_multiplier = 0.015

    def __init__(
        self,
        start=LEFT,
        end=RIGHT,
        buff=MED_SMALL_BUFF,
        path_arc=0,
        fill_color=None,
        fill_opacity=1.0,
        stroke_width=0,
        thickness=3.0,
        tip_width_ratio=5.0,
        tip_angle=PI / 3,
        max_tip_length_to_length_ratio=0.5,
        max_width_to_length_ratio=0.1,
        semantic_type="geometric_shape",
        semantic_role="arrow",
        semantic_content=None,
        **kwargs
    ):
        self.max_tip_length_to_length_ratio = max_tip_length_to_length_ratio
        self.max_width_to_length_ratio = max_width_to_length_ratio
        self.tip_width_ratio = tip_width_ratio
        self.tip_angle = tip_angle
        self.thickness = float(thickness)

        if fill_color is None:
            fill_color = kwargs.get("color", WHITE)

        super().__init__(
            start=start,
            end=end,
            buff=buff,
            path_arc=path_arc,
            stroke_width=stroke_width,
            **kwargs
        )

        self.set_fill(fill_color, opacity=fill_opacity)
        self.set_stroke(width=stroke_width)

        self._semantic_type = ""
        self._semantic_role = ""
        self._semantic_content = None
        self.semantic_type = semantic_type
        self.semantic_role = semantic_role
        self.semantic_content = semantic_content

        self.set_thickness(thickness)

    @property
    def semantic_type(self):
        return self._semantic_type

    @semantic_type.setter
    def semantic_type(self, value):
        if not isinstance(value, str):
            raise TypeError("semantic_type must be a string")
        if not value.strip():
            raise ValueError("semantic_type cannot be empty")
        self._semantic_type = value

    @property
    def semantic_role(self):
        return self._semantic_role

    @semantic_role.setter
    def semantic_role(self, value):
        if not isinstance(value, str):
            raise TypeError("semantic_role must be a string")
        if not value.strip():
            raise ValueError("semantic_role cannot be empty")
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

    def get_key_dimensions(self, length):
        if length <= 0:
            return {
                "length": 0.0,
                "tip_length": 0.0,
                "shaft_width": 0.0,
                "tip_width": 0.0,
            }

        shaft_width = min(
            self.thickness * self.tickness_multiplier,
            self.max_width_to_length_ratio * length,
        )
        tip_width = self.tip_width_ratio * shaft_width
        max_tip_length = self.max_tip_length_to_length_ratio * length

        if tip_width <= 0 or self.tip_angle <= 0:
            tip_length = min(max_tip_length, 0.25 * length)
        else:
            tip_length = min(
                max_tip_length,
                tip_width / (2 * np.tan(self.tip_angle / 2)),
            )

        return {
            "length": float(length),
            "tip_length": float(max(tip_length, 0.0)),
            "shaft_width": float(max(shaft_width, 0.0)),
            "tip_width": float(max(tip_width, 0.0)),
        }

    def set_points_by_ends(self, start, end, buff=0, path_arc=0):
        super().set_points_by_ends(start, end, buff=buff, path_arc=path_arc)
        self.set_thickness(self.thickness)
        return self

    def get_start(self):
        return super().get_start()

    def get_end(self):
        return super().get_end()

    def get_start_and_end(self):
        return self.get_start(), self.get_end()

    def put_start_and_end_on(self, start, end):
        super().put_start_and_end_on(start, end)
        self.set_thickness(self.thickness)
        return self

    def scale(self, scale_factor, **kwargs):
        super().scale(scale_factor, **kwargs)
        self.set_thickness(self.thickness * scale_factor)
        return self

    def set_thickness(self, thickness):
        self.thickness = float(thickness)
        length = self.get_length()
        dims = self.get_key_dimensions(length)
        shaft_width = dims["shaft_width"]
        tip_length = dims["tip_length"]

        self.set_stroke(width=0)
        if shaft_width > 0:
            self.set_width(shaft_width, about_point=self.get_center(), stretch=True)

        if tip_length > 0 and length > 0:
            self.add_tip(
                tip_length=tip_length,
                tip_width=dims["tip_width"],
                at_start=False
            )
        return self


def KinematicsArrow(start=LEFT, end=RIGHT, semantic_content=None, **kwargs):
    return Arrow(
        start=start,
        end=end,
        semantic_type="geometric_shape",
        semantic_role="kinematics_vector",
        semantic_content=semantic_content,
        **kwargs
    )


def ForceArrow(start=ORIGIN, end=RIGHT, semantic_content="F", **kwargs):
    return Arrow(
        start=start,
        end=end,
        semantic_type="geometric_shape",
        semantic_role="gravitational_force",
        semantic_content=semantic_content,
        **kwargs
    )


def VelocityArrow(start=ORIGIN, end=RIGHT, semantic_content="v", **kwargs):
    return Arrow(
        start=start,
        end=end,
        semantic_type="geometric_shape",
        semantic_role="velocity_vector",
        semantic_content=semantic_content,
        **kwargs
    )