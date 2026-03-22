from manimlib import *


class SemanticMixin(object):
    DEFAULT_SEMANTIC_TYPE = ""
    DEFAULT_SEMANTIC_ROLE = ""
    DEFAULT_SEMANTIC_CONTENT = None

    def _init_semantics(
        self,
        semantic_type="",
        semantic_role="",
        semantic_content=None,
    ):
        self.semantic_type = semantic_type if semantic_type != "" else self.DEFAULT_SEMANTIC_TYPE
        self.semantic_role = semantic_role if semantic_role != "" else self.DEFAULT_SEMANTIC_ROLE
        self.semantic_content = semantic_content if semantic_content is not None else self.DEFAULT_SEMANTIC_CONTENT

    @property
    def semantic_type(self):
        return getattr(self, "_semantic_type", "")

    @semantic_type.setter
    def semantic_type(self, value):
        if value is None:
            value = ""
        if not isinstance(value, str):
            raise TypeError("semantic_type must be a string")
        self._semantic_type = value

    @property
    def semantic_role(self):
        return getattr(self, "_semantic_role", "")

    @semantic_role.setter
    def semantic_role(self, value):
        if value is None:
            value = ""
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


class TimeVaryingVectorField(VectorField, SemanticMixin):
    DEFAULT_SEMANTIC_TYPE = "vector_field"
    DEFAULT_SEMANTIC_ROLE = "time_varying_vector_field"
    DEFAULT_SEMANTIC_CONTENT = None

    def __init__(
        self,
        time_func,
        coordinate_system,
        semantic_type="vector_field",
        semantic_role="time_varying_vector_field",
        semantic_content=None,
        **kwargs
    ):
        if not callable(time_func):
            raise TypeError("time_func must be callable")
        if coordinate_system is None:
            raise ValueError("coordinate_system must not be None")

        self.time_func = time_func
        self.coordinate_system = coordinate_system
        self.time = 0.0

        initial_func = self._get_vector_func_for_time(self.time)
        VectorField.__init__(self, initial_func, coordinate_system, **kwargs)
        self._init_semantics(
            semantic_type=semantic_type,
            semantic_role=semantic_role,
            semantic_content=semantic_content,
        )

    def _get_vector_func_for_time(self, time_value):
        def vector_func(point):
            return self.time_func(point, time_value)
        return vector_func

    def increment_time(self, dt):
        if not isinstance(dt, (int, float)):
            raise TypeError("dt must be a number")
        self.time += dt
        self.func = self._get_vector_func_for_time(self.time)
        if hasattr(self, "submobjects"):
            for submob in self.submobjects:
                if hasattr(submob, "reset_points"):
                    submob.reset_points()
        self.update_vectors()
        return self

    def copy(self, **kwargs):
        new_obj = super().copy(**kwargs)
        new_obj._semantic_type = getattr(self, "_semantic_type", "")
        new_obj._semantic_role = getattr(self, "_semantic_role", "")
        new_obj._semantic_content = getattr(self, "_semantic_content", None)
        new_obj.time_func = self.time_func
        new_obj.coordinate_system = self.coordinate_system
        new_obj.time = self.time
        return new_obj


def KinematicsTimeVaryingVectorField(time_func, coordinate_system, **kwargs):
    return TimeVaryingVectorField(
        time_func,
        coordinate_system,
        semantic_type="vector_field",
        semantic_role="kinematics_vector_field",
        **kwargs
    )


def ElectricFieldTimeVaryingVectorField(time_func, coordinate_system, **kwargs):
    return TimeVaryingVectorField(
        time_func,
        coordinate_system,
        semantic_type="vector_field",
        semantic_role="electric_field_line",
        **kwargs
    )


def FlowFieldTimeVaryingVectorField(time_func, coordinate_system, **kwargs):
    return TimeVaryingVectorField(
        time_func,
        coordinate_system,
        semantic_type="vector_field",
        semantic_role="flow_field",
        **kwargs
    )