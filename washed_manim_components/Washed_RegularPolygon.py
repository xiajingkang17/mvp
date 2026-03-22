from manimlib import *
import math


class RegularPolygon(Polygon):
    def __init__(
        self,
        n=6,
        radius=1.0,
        start_angle=None,
        semantic_type="geometric_shape",
        semantic_role="regular_polygon",
        semantic_content=None,
        **kwargs
    ):
        self._semantic_type = ""
        self._semantic_role = ""
        self._semantic_content = None

        n = self._validate_n(n)
        radius = self._validate_radius(radius)

        if start_angle is None:
            start_angle = 0 if n % 2 == 0 else 90 * DEGREES
        start_angle = self._validate_angle(start_angle)

        vertices = [
            radius * np.array([
                math.cos(start_angle + k * TAU / n),
                math.sin(start_angle + k * TAU / n),
                0.0,
            ])
            for k in range(n)
        ]

        super().__init__(*vertices, **kwargs)

        self.n = n
        self.radius = radius
        self.start_angle = start_angle

        if semantic_content is None:
            semantic_content = "n={0}, r={1}".format(self.n, self.radius)

        self.semantic_type = semantic_type
        self.semantic_role = semantic_role
        self.semantic_content = semantic_content

    @staticmethod
    def _validate_n(value):
        if not isinstance(value, int):
            raise TypeError("n must be an integer")
        if value < 3:
            raise ValueError("n must be at least 3")
        return value

    @staticmethod
    def _validate_radius(value):
        if not isinstance(value, (int, float)):
            raise TypeError("radius must be a number")
        value = float(value)
        if value <= 0:
            raise ValueError("radius must be positive")
        return value

    @staticmethod
    def _validate_angle(value):
        if not isinstance(value, (int, float)):
            raise TypeError("start_angle must be a number")
        return float(value)

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
        new_obj.n = getattr(self, "n", 6)
        new_obj.radius = getattr(self, "radius", 1.0)
        new_obj.start_angle = getattr(self, "start_angle", 0.0)
        return new_obj

    def get_bbox(self):
        points = self.get_points()
        if len(points) == 0:
            zero = np.zeros(3)
            return np.array([zero, zero])
        mins = np.min(points, axis=0)
        maxs = np.max(points, axis=0)
        return np.array([mins, maxs])


def EquilateralTriangle(radius=1.0, start_angle=PI / 2, **kwargs):
    return RegularPolygon(
        n=3,
        radius=radius,
        start_angle=start_angle,
        semantic_role="triangle",
        semantic_content="equilateral_triangle",
        **kwargs
    )


def SquarePolygon(radius=1.0, start_angle=PI / 4, **kwargs):
    return RegularPolygon(
        n=4,
        radius=radius,
        start_angle=start_angle,
        semantic_role="square",
        semantic_content="square",
        **kwargs
    )


def HexagonPolygon(radius=1.0, start_angle=0.0, **kwargs):
    return RegularPolygon(
        n=6,
        radius=radius,
        start_angle=start_angle,
        semantic_role="hexagon",
        semantic_content="regular_hexagon",
        **kwargs
    )