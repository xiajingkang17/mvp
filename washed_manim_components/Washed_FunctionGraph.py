from manimlib import *


class FunctionGraph(ParametricCurve):
    def __init__(
        self,
        function,
        x_range=None,
        color=YELLOW,
        semantic_role="function_graph",
        semantic_content=None,
        **kwargs
    ):
        if not callable(function):
            raise TypeError("function must be callable")

        if x_range is None:
            x_range = (-8, 8, 0.25)

        normalized_x_range = self._normalize_x_range(x_range)

        self.function = function
        self.x_range = normalized_x_range

        self._semantic_type = "function_curve"
        self._semantic_role = ""
        self._semantic_content = None

        super().__init__(
            self._parameter_function,
            t_range=normalized_x_range,
            color=color,
            **kwargs
        )

        self.semantic_type = "function_curve"
        self.semantic_role = semantic_role
        self.semantic_content = semantic_content

    @staticmethod
    def _normalize_x_range(x_range):
        if not isinstance(x_range, (list, tuple)):
            raise TypeError("x_range must be a list or tuple")

        if len(x_range) == 2:
            x_min, x_max = x_range
            step = 0.25
        elif len(x_range) == 3:
            x_min, x_max, step = x_range
        else:
            raise ValueError("x_range must have length 2 or 3")

        if not all(isinstance(value, (int, float)) for value in (x_min, x_max, step)):
            raise TypeError("x_range values must be numeric")

        if step == 0:
            raise ValueError("x_range step cannot be zero")

        if x_min == x_max:
            raise ValueError("x_range min and max cannot be equal")

        if x_max > x_min and step < 0:
            step = abs(step)
        elif x_max < x_min and step > 0:
            step = -step

        return (x_min, x_max, step)

    def _parameter_function(self, t):
        return np.array([t, self.function(t), 0.0])

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
        if hasattr(self, "function"):
            new_obj.function = self.function
        if hasattr(self, "x_range"):
            new_obj.x_range = self.x_range
        return new_obj

    def get_bbox(self):
        return np.array(self.get_bounding_box())

    def set_semantic_labels(self, semantic_type=None, semantic_role=None, semantic_content=None):
        if semantic_type is not None:
            self.semantic_type = semantic_type
        if semantic_role is not None:
            self.semantic_role = semantic_role
        if semantic_content is not None or semantic_content is None:
            self.semantic_content = semantic_content
        return self


def KinematicsFunctionGraph(function, x_range=None, color=BLUE, semantic_content=None, **kwargs):
    return FunctionGraph(
        function=function,
        x_range=x_range,
        color=color,
        semantic_role="kinematics_curve",
        semantic_content=semantic_content,
        **kwargs
    )


def QuadraticFunctionGraph(a=1.0, b=0.0, c=0.0, x_range=None, color=GREEN, **kwargs):
    return FunctionGraph(
        function=lambda x: a * x * x + b * x + c,
        x_range=x_range,
        color=color,
        semantic_role="quadratic_function_curve",
        semantic_content=f"y = {a}x^2 + {b}x + {c}",
        **kwargs
    )


def SineFunctionGraph(amplitude=1.0, omega=1.0, phase=0.0, x_range=None, color=YELLOW, **kwargs):
    return FunctionGraph(
        function=lambda x: amplitude * np.sin(omega * x + phase),
        x_range=x_range,
        color=color,
        semantic_role="trigonometric_function_curve",
        semantic_content=f"y = {amplitude}sin({omega}x + {phase})",
        **kwargs
    )