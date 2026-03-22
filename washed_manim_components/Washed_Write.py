from manimlib import *


class Write(DrawBorderThenFill):
    def __init__(
        self,
        vmobject,
        run_time=None,
        lag_ratio=None,
        rate_func=linear,
        stroke_color=None,
        semantic_type="animation",
        semantic_role="write_animation",
        semantic_content=None,
        **kwargs
    ):
        self._semantic_type = ""
        self._semantic_role = ""
        self._semantic_content = None

        self.semantic_type = semantic_type
        self.semantic_role = semantic_role
        self.semantic_content = semantic_content

        family_size = len(vmobject.family_members_with_points())
        computed_run_time = self.compute_run_time(family_size, run_time)
        computed_lag_ratio = self.compute_lag_ratio(family_size, lag_ratio)

        super().__init__(
            vmobject,
            run_time=computed_run_time,
            lag_ratio=computed_lag_ratio,
            rate_func=rate_func,
            stroke_color=stroke_color,
            **kwargs
        )

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

    def compute_run_time(self, family_size, run_time):
        if run_time is not None:
            return run_time
        if family_size < 15:
            return 1
        return 2

    def compute_lag_ratio(self, family_size, lag_ratio):
        if lag_ratio is not None:
            return lag_ratio
        if family_size == 0:
            return 0
        return min(4.0 / family_size, 0.2)

    def copy(self, **kwargs):
        new_obj = super().copy(**kwargs)
        new_obj._semantic_type = getattr(self, "_semantic_type", "")
        new_obj._semantic_role = getattr(self, "_semantic_role", "")
        new_obj._semantic_content = getattr(self, "_semantic_content", None)
        return new_obj


def PhysicsWrite(vmobject, semantic_content=None, **kwargs):
    return Write(
        vmobject,
        semantic_type="animation",
        semantic_role="physics_annotation_write",
        semantic_content=semantic_content,
        **kwargs
    )


def MathWrite(vmobject, semantic_content=None, **kwargs):
    return Write(
        vmobject,
        semantic_type="animation",
        semantic_role="math_expression_write",
        semantic_content=semantic_content,
        **kwargs
    )


def LabelWrite(vmobject, semantic_content=None, **kwargs):
    return Write(
        vmobject,
        semantic_type="animation",
        semantic_role="label_write",
        semantic_content=semantic_content,
        **kwargs
    )