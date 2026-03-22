from manimlib import *


class DashedLine(Line):
    CONFIG = {
        "dash_length": 0.2,
        "positive_space_ratio": 0.5,
        "semantic_type": "geometric_shape",
        "semantic_role": "dashed_line",
        "semantic_content": None,
    }

    def __init__(
        self,
        start=LEFT,
        end=RIGHT,
        dash_length=None,
        positive_space_ratio=None,
        semantic_type=None,
        semantic_role=None,
        semantic_content=None,
        **kwargs
    ):
        Line.__init__(self, start=start, end=end, **kwargs)

        if dash_length is None:
            dash_length = self.CONFIG["dash_length"]
        if positive_space_ratio is None:
            positive_space_ratio = self.CONFIG["positive_space_ratio"]

        self.semantic_type = semantic_type if semantic_type is not None else self.CONFIG["semantic_type"]
        self.semantic_role = semantic_role if semantic_role is not None else self.CONFIG["semantic_role"]
        self.semantic_content = semantic_content if semantic_content is not None else self.CONFIG["semantic_content"]

        self.dash_length = float(dash_length)
        self.positive_space_ratio = float(positive_space_ratio)

        self._base_start = np.array(self.get_start())
        self._base_end = np.array(self.get_end())
        self._base_color = self.get_color()
        self._build_dashes()

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

    def _build_dashes(self):
        start = np.array(self._base_start)
        end = np.array(self._base_end)
        color = self._base_color

        self.clear_points()
        self.submobjects = []

        line_vect = end - start
        line_length = get_norm(line_vect)
        if line_length == 0:
            return self

        direction = normalize(line_vect)
        num_dashes = self.calculate_num_dashes(self.dash_length, self.positive_space_ratio)
        if num_dashes <= 0:
            return self

        full_step = line_length / num_dashes
        dash_portion = np.clip(self.positive_space_ratio, 0.0, 1.0)
        visible_length = full_step * dash_portion

        for index in range(num_dashes):
            dash_start = start + direction * (index * full_step)
            dash_end = dash_start + direction * visible_length
            dash = Line(dash_start, dash_end)
            dash.match_style(self)
            dash.set_color(color)
            self.add(dash)

        return self

    def calculate_num_dashes(self, dash_length, positive_space_ratio) -> int:
        if dash_length <= 0:
            raise ValueError("dash_length must be positive")
        if not (0 < positive_space_ratio <= 1):
            raise ValueError("positive_space_ratio must be in the interval (0, 1]")

        length = get_norm(self._base_end - self._base_start)
        if length == 0:
            return 0

        effective_dash_length = dash_length / positive_space_ratio
        return max(1, int(np.ceil(length / effective_dash_length)))

    def get_start(self):
        return np.array(self._base_start)

    def get_end(self):
        return np.array(self._base_end)

    def get_start_and_end(self):
        return self.get_start(), self.get_end()

    def get_first_handle(self):
        if len(self.submobjects) > 0:
            return self.submobjects[0].get_end()
        return self.get_start()

    def get_last_handle(self):
        if len(self.submobjects) > 0:
            return self.submobjects[-1].get_start()
        return self.get_end()

    def put_start_and_end_on(self, start, end):
        self._base_start = np.array(start)
        self._base_end = np.array(end)
        self._build_dashes()
        return self

    def set_color(self, color, family=True):
        super().set_color(color, family=family)
        self._base_color = self.get_color()
        return self

    def get_bbox(self):
        return self.get_bounding_box()

    def copy(self, **kwargs):
        new_obj = super().copy(**kwargs)
        new_obj._semantic_type = getattr(self, "_semantic_type", "")
        new_obj._semantic_role = getattr(self, "_semantic_role", "")
        new_obj._semantic_content = getattr(self, "_semantic_content", None)
        new_obj.dash_length = getattr(self, "dash_length", self.CONFIG["dash_length"])
        new_obj.positive_space_ratio = getattr(self, "positive_space_ratio", self.CONFIG["positive_space_ratio"])
        new_obj._base_start = np.array(getattr(self, "_base_start", self.get_start()))
        new_obj._base_end = np.array(getattr(self, "_base_end", self.get_end()))
        new_obj._base_color = getattr(self, "_base_color", self.get_color())
        return new_obj


def KinematicsDashedLine(start=LEFT, end=RIGHT, **kwargs):
    return DashedLine(
        start=start,
        end=end,
        semantic_type="geometric_shape",
        semantic_role="kinematics_reference_line",
        **kwargs
    )


def SymmetryDashedLine(start=DOWN, end=UP, **kwargs):
    return DashedLine(
        start=start,
        end=end,
        semantic_type="geometric_shape",
        semantic_role="symmetry_axis",
        **kwargs
    )


def ProjectionDashedLine(start=ORIGIN, end=RIGHT + UP, **kwargs):
    return DashedLine(
        start=start,
        end=end,
        semantic_type="geometric_shape",
        semantic_role="projection_line",
        **kwargs
    )