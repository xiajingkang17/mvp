from manimlib import *


class SemanticMixin(object):
    def _init_semantics(
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


class Ellipse(Circle, SemanticMixin):
    def __init__(
        self,
        width=2.0,
        height=1.0,
        arc_center=ORIGIN,
        semantic_type="geometric_shape",
        semantic_role="ellipse",
        semantic_content=None,
        **kwargs
    ):
        if not isinstance(width, (int, float)) or width <= 0:
            raise ValueError("width must be a positive number")
        if not isinstance(height, (int, float)) or height <= 0:
            raise ValueError("height must be a positive number")

        super().__init__(**kwargs)
        self.set_width(float(width), stretch=True)
        self.set_height(float(height), stretch=True)
        self.move_to(arc_center)
        self._init_semantics(
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


def KinematicsEllipse(width=3.0, height=1.5, **kwargs):
    return Ellipse(
        width=width,
        height=height,
        semantic_type="geometric_shape",
        semantic_role="kinematics_orbit",
        **kwargs
    )


def GeometryFocusEllipse(width=4.0, height=2.0, semantic_content="ellipse", **kwargs):
    return Ellipse(
        width=width,
        height=height,
        semantic_type="geometric_shape",
        semantic_role="conic_section",
        semantic_content=semantic_content,
        **kwargs
    )


def ChargeDistributionEllipse(width=3.5, height=2.0, **kwargs):
    return Ellipse(
        width=width,
        height=height,
        semantic_type="geometric_shape",
        semantic_role="charge_distribution_boundary",
        **kwargs
    )