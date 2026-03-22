from manimlib import *


class Triangle(RegularPolygon):
    def __init__(
        self,
        start_angle=0,
        semantic_type="geometric_shape",
        semantic_role="triangle",
        semantic_content=None,
        **kwargs
    ):
        super().__init__(n=3, start_angle=start_angle, **kwargs)
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
        if not value:
            raise ValueError("semantic_type cannot be empty")
        self._semantic_type = value

    @property
    def semantic_role(self):
        return getattr(self, "_semantic_role", "")

    @semantic_role.setter
    def semantic_role(self, value):
        if not isinstance(value, str):
            raise TypeError("semantic_role must be a string")
        if not value:
            raise ValueError("semantic_role cannot be empty")
        self._semantic_role = value

    @property
    def semantic_content(self):
        return getattr(self, "_semantic_content", None)

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


def EquilateralTriangle(**kwargs):
    return Triangle(
        semantic_role="equilateral_triangle",
        semantic_content="all sides equal",
        **kwargs
    )


def RightTriangle(**kwargs):
    triangle = Triangle(**kwargs)
    triangle.semantic_role = "right_triangle"
    triangle.semantic_content = "one angle is 90 degrees"
    return triangle


def PhysicsVectorTriangle(**kwargs):
    triangle = Triangle(**kwargs)
    triangle.semantic_role = "vector_decomposition_triangle"
    triangle.semantic_content = "force or velocity decomposition"
    return triangle