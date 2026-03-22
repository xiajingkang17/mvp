from manimlib import *


class SemanticApplyFunction(Transform):
    def __init__(
        self,
        function,
        mobject,
        semantic_type="geometric_shape",
        semantic_role="transformed_object",
        semantic_content=None,
        **kwargs
    ):
        if not callable(function):
            raise TypeError("function must be callable")
        if not isinstance(mobject, Mobject):
            raise TypeError("mobject must be an instance of Mobject")

        self.function = function
        self.mobject = mobject

        self._semantic_type = ""
        self._semantic_role = ""
        self._semantic_content = None
        self.semantic_type = semantic_type
        self.semantic_role = semantic_role
        self.semantic_content = semantic_content

        super().__init__(mobject, **kwargs)

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

    def create_target(self):
        target = self.mobject.copy()
        transformed = self.function(target)
        if transformed is None:
            transformed = target
        if not isinstance(transformed, Mobject):
            raise TypeError("function must return a Mobject or None")
        return transformed

    def copy(self, **kwargs):
        new_obj = super().copy(**kwargs)
        new_obj._semantic_type = getattr(self, "_semantic_type", "")
        new_obj._semantic_role = getattr(self, "_semantic_role", "")
        new_obj._semantic_content = getattr(self, "_semantic_content", None)
        new_obj.function = getattr(self, "function", None)
        return new_obj


def ApplyPointwiseFunction(function, mobject, **kwargs):
    return SemanticApplyFunction(
        function=function,
        mobject=mobject,
        semantic_type="geometric_shape",
        semantic_role="pointwise_transform",
        semantic_content=getattr(function, "__name__", None),
        **kwargs
    )


def ApplyKinematicsTransform(function, mobject, **kwargs):
    return SemanticApplyFunction(
        function=function,
        mobject=mobject,
        semantic_type="function_curve",
        semantic_role="kinematics_curve",
        semantic_content=getattr(function, "__name__", None),
        **kwargs
    )


def ApplyGeometricTransform(function, mobject, **kwargs):
    return SemanticApplyFunction(
        function=function,
        mobject=mobject,
        semantic_type="geometric_shape",
        semantic_role="geometric_transform",
        semantic_content=getattr(function, "__name__", None),
        **kwargs
    )