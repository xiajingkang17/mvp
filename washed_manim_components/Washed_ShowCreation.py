from manimlib import *


class ShowCreation(ShowPartial):
    def __init__(
        self,
        mobject,
        lag_ratio=1,
        semantic_type="animation",
        semantic_role="show_creation",
        semantic_content=None,
        **kwargs
    ):
        self._semantic_type = ""
        self._semantic_role = ""
        self._semantic_content = None
        self.semantic_type = semantic_type
        self.semantic_role = semantic_role
        self.semantic_content = semantic_content
        super().__init__(mobject, lag_ratio=lag_ratio, **kwargs)

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

    def get_bounds(self, alpha) -> tuple[float, float]:
        alpha = clip(alpha, 0, 1)
        return (0, alpha)

    def copy(self, **kwargs):
        new_obj = super().copy(**kwargs)
        new_obj._semantic_type = getattr(self, "_semantic_type", "")
        new_obj._semantic_role = getattr(self, "_semantic_role", "")
        new_obj._semantic_content = getattr(self, "_semantic_content", None)
        return new_obj


def PhysicsShowCreation(mobject, semantic_content=None, **kwargs):
    return ShowCreation(
        mobject,
        semantic_type="animation",
        semantic_role="physics_diagram_creation",
        semantic_content=semantic_content,
        **kwargs
    )


def MathShowCreation(mobject, semantic_content=None, **kwargs):
    return ShowCreation(
        mobject,
        semantic_type="animation",
        semantic_role="math_object_creation",
        semantic_content=semantic_content,
        **kwargs
    )


def CoordinateSystemShowCreation(mobject, semantic_content=None, **kwargs):
    return ShowCreation(
        mobject,
        semantic_type="animation",
        semantic_role="coordinate_system_creation",
        semantic_content=semantic_content,
        **kwargs
    )