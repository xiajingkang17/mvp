from manimlib import *

try:
    import numpy as np
except ImportError:  # pragma: no cover
    np = None


class Polygon(VMobject):
    """
    Creates a polygon by joining the specified vertices.
    """

    def __init__(
        self,
        *vertices,
        color=WHITE,
        semantic_type="geometric_shape",
        semantic_role="polygon",
        semantic_content=None,
        **kwargs
    ):
        super().__init__(color=color, **kwargs)
        self._semantic_type = ""
        self._semantic_role = ""
        self._semantic_content = None
        self.semantic_type = semantic_type
        self.semantic_role = semantic_role
        self.semantic_content = semantic_content

        self._vertices = []
        if vertices:
            self.set_vertices(*vertices)

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

    def copy(self, **kwargs):
        new_obj = super().copy(**kwargs)
        new_obj._semantic_type = getattr(self, "_semantic_type", "")
        new_obj._semantic_role = getattr(self, "_semantic_role", "")
        new_obj._semantic_content = getattr(self, "_semantic_content", None)
        if hasattr(self, "_vertices"):
            new_obj._vertices = [np.array(vertex) for vertex in self._vertices]
        return new_obj

    def _to_point(self, vertex):
        if np is None:
            raise ImportError("numpy is required to construct Polygon")
        point = np.array(vertex, dtype=float)
        if point.shape != (3,):
            raise ValueError("Each vertex must be a 3D point")
        return point

    def set_vertices(self, *vertices):
        if len(vertices) < 3:
            raise ValueError("Polygon requires at least 3 vertices")
        self._vertices = [self._to_point(vertex) for vertex in vertices]
        self.clear_points()
        self.start_new_path(self._vertices[0])
        for vertex in self._vertices[1:]:
            self.add_line_to(vertex)
        self.close_path()
        return self

    def get_vertices(self):
        if not hasattr(self, "_vertices") or len(self._vertices) == 0:
            return np.zeros((0, 3)) if np is not None else []
        return np.array(self._vertices)

    def get_bbox(self):
        return np.array(self.get_bounding_box())

    def round_corners(self, radius):
        if radius == 0:
            return self
        vertices = self.get_vertices()
        if len(vertices) < 3:
            return self

        if np is None:
            raise ImportError("numpy is required to round Polygon corners")

        arcs = []
        n = len(vertices)
        for i in range(n):
            v1 = vertices[i - 1]
            v2 = vertices[i]
            v3 = vertices[(i + 1) % n]

            vect1 = normalize(v1 - v2)
            vect2 = normalize(v3 - v2)
            angle = angle_between_vectors(vect1, vect2)

            if np.isclose(angle, 0) or np.isclose(angle, PI):
                continue

            cut_off_length = radius * np.tan(angle / 2)
            cut_off_length = min(
                cut_off_length,
                0.5 * get_norm(v1 - v2),
                0.5 * get_norm(v3 - v2),
            )

            sign = np.sign(radius)
            arc = ArcBetweenPoints(
                v2 + cut_off_length * vect1,
                v2 + cut_off_length * vect2,
                angle=sign * angle,
            )
            arcs.append(arc)

        if len(arcs) == 0:
            return self

        self.clear_points()
        for i, arc in enumerate(arcs):
            if i == 0:
                self.append_points(arc.get_points())
            else:
                line = Line(arcs[i - 1].get_end(), arc.get_start())
                self.add_line_to(line.get_end())
                self.append_points(arc.get_points())
        line = Line(arcs[-1].get_end(), arcs[0].get_start())
        self.add_line_to(line.get_end())
        self.close_path()
        return self


def Triangle(
    p1=LEFT + DOWN,
    p2=RIGHT + DOWN,
    p3=UP,
    semantic_content=None,
    **kwargs
):
    return Polygon(
        p1,
        p2,
        p3,
        semantic_type="geometric_shape",
        semantic_role="triangle",
        semantic_content=semantic_content,
        **kwargs
    )


def RectanglePolygon(
    width=4.0,
    height=2.0,
    semantic_content=None,
    **kwargs
):
    hw = width / 2.0
    hh = height / 2.0
    return Polygon(
        np.array([-hw, -hh, 0.0]),
        np.array([hw, -hh, 0.0]),
        np.array([hw, hh, 0.0]),
        np.array([-hw, hh, 0.0]),
        semantic_type="geometric_shape",
        semantic_role="rectangle",
        semantic_content=semantic_content,
        **kwargs
    )


def RegularPolygonForMath(
    n=6,
    radius=2.0,
    start_angle=0.0,
    semantic_content=None,
    **kwargs
):
    if np is None:
        raise ImportError("numpy is required to construct RegularPolygonForMath")
    if not isinstance(n, int) or n < 3:
        raise ValueError("n must be an integer greater than or equal to 3")
    vertices = []
    for k in range(n):
        angle = start_angle + TAU * k / n
        vertices.append(
            np.array([
                radius * np.cos(angle),
                radius * np.sin(angle),
                0.0
            ])
        )
    return Polygon(
        *vertices,
        semantic_type="geometric_shape",
        semantic_role="regular_polygon",
        semantic_content=semantic_content if semantic_content is not None else str(n),
        **kwargs
    )