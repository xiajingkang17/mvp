from manimlib import *


class Rectangle(Polygon):
    def __init__(
        self,
        width=4.0,
        height=2.0,
        color=WHITE,
        semantic_role="rectangle",
        semantic_content=None,
        **kwargs
    ):
        self._semantic_type = "geometric_shape"
        self._semantic_role = ""
        self._semantic_content = None

        half_width = width / 2
        half_height = height / 2
        points = [
            UL * half_height + LEFT * (half_width - half_height),
            UR * half_height + RIGHT * (half_width - half_height),
            DR * half_height + RIGHT * (half_width - half_height),
            DL * half_height + LEFT * (half_width - half_height),
        ]
        points = [
            np.array([-half_width, half_height, 0.0]),
            np.array([half_width, half_height, 0.0]),
            np.array([half_width, -half_height, 0.0]),
            np.array([-half_width, -half_height, 0.0]),
        ]
        super().__init__(*points, color=color, **kwargs)

        self.semantic_type = "geometric_shape"
        self.semantic_role = semantic_role
        self.semantic_content = semantic_content

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
        return new_obj

    def surround(self, mobject, buff=SMALL_BUFF):
        if buff < 0:
            raise ValueError("buff must be non-negative")
        self.set_width(mobject.get_width() + 2 * buff, stretch=True)
        self.set_height(mobject.get_height() + 2 * buff, stretch=True)
        self.move_to(mobject)
        return self

    def get_bbox(self):
        return np.array(self.get_bounding_box())


def PhysicsRectangle(width=4.0, height=2.0, semantic_content=None, **kwargs):
    return Rectangle(
        width=width,
        height=height,
        semantic_role="physics_region",
        semantic_content=semantic_content,
        **kwargs
    )


def GeometryRectangle(width=4.0, height=2.0, semantic_content=None, **kwargs):
    return Rectangle(
        width=width,
        height=height,
        semantic_role="geometry_rectangle",
        semantic_content=semantic_content,
        **kwargs
    )


def PlotFrameRectangle(width=6.0, height=4.0, semantic_content=None, **kwargs):
    return Rectangle(
        width=width,
        height=height,
        semantic_role="plot_frame",
        semantic_content=semantic_content,
        **kwargs
    )