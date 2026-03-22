from manimlib import *


class ComplexPlane(NumberPlane):
    def __init__(
        self,
        x_range=None,
        y_range=None,
        background_line_style=None,
        faded_line_style=None,
        faded_line_ratio=4,
        make_smooth_after_applying_functions=True,
        semantic_type="coordinate_system",
        semantic_role="complex_plane",
        semantic_content=None,
        **kwargs
    ):
        if x_range is None:
            x_range = (-8.0, 8.0, 1.0)
        if y_range is None:
            y_range = (-4.0, 4.0, 1.0)

        super().__init__(
            x_range=x_range,
            y_range=y_range,
            background_line_style=background_line_style,
            faded_line_style=faded_line_style,
            faded_line_ratio=faded_line_ratio,
            make_smooth_after_applying_functions=make_smooth_after_applying_functions,
            **kwargs
        )

        self._semantic_type = ""
        self._semantic_role = ""
        self._semantic_content = None
        self.semantic_type = semantic_type
        self.semantic_role = semantic_role
        self.semantic_content = semantic_content

        self.coordinate_labels = VGroup()

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
        if hasattr(self, "coordinate_labels"):
            new_obj.coordinate_labels = self.coordinate_labels.copy()
        return new_obj

    def number_to_point(self, number):
        z = complex(number)
        return self.coords_to_point(z.real, z.imag)

    def n2p(self, number):
        return self.number_to_point(number)

    def point_to_number(self, point):
        x, y = self.point_to_coords(point)
        return complex(x, y)

    def p2n(self, point):
        return self.point_to_number(point)

    def get_unit_size(self):
        x_values = getattr(self.x_axis, "x_range", [0.0, 1.0, 1.0])
        step = x_values[2] if len(x_values) >= 3 and x_values[2] != 0 else 1.0
        p0 = self.coords_to_point(0, 0)
        p1 = self.coords_to_point(step, 0)
        return get_norm(p1 - p0) / abs(step)

    def get_default_coordinate_values(self, skip_first=True):
        values = []

        x_range = getattr(self.x_axis, "x_range", [0.0, 1.0, 1.0])
        y_range = getattr(self.y_axis, "x_range", [0.0, 1.0, 1.0])

        x_start, x_end, x_step = x_range[:3]
        y_start, y_end, y_step = y_range[:3]

        if x_step == 0:
            x_step = 1.0
        if y_step == 0:
            y_step = 1.0

        x_values = np.arange(x_start, x_end + 0.5 * x_step, x_step)
        y_values = np.arange(y_start, y_end + 0.5 * y_step, y_step)

        for x in x_values:
            if skip_first and abs(x) < 1e-8:
                continue
            values.append(complex(float(x), 0.0))

        for y in y_values:
            if skip_first and abs(y) < 1e-8:
                continue
            values.append(complex(0.0, float(y)))

        return values

    def _format_complex_label(self, number):
        z = complex(number)
        real = z.real
        imag = z.imag

        if abs(imag) < 1e-8:
            if abs(real - round(real)) < 1e-8:
                return str(int(round(real)))
            return str(real)

        if abs(real) < 1e-8:
            if abs(imag - 1) < 1e-8:
                return "i"
            if abs(imag + 1) < 1e-8:
                return "-i"
            if abs(imag - round(imag)) < 1e-8:
                return f"{int(round(imag))}i"
            return f"{imag}i"

        real_str = str(int(round(real))) if abs(real - round(real)) < 1e-8 else str(real)
        if abs(imag - 1) < 1e-8:
            imag_str = "+i"
        elif abs(imag + 1) < 1e-8:
            imag_str = "-i"
        elif imag > 0:
            imag_core = str(int(round(imag))) if abs(imag - round(imag)) < 1e-8 else str(imag)
            imag_str = f"+{imag_core}i"
        else:
            imag_core = str(int(round(abs(imag)))) if abs(abs(imag) - round(abs(imag))) < 1e-8 else str(abs(imag))
            imag_str = f"-{imag_core}i"
        return real_str + imag_str

    def add_coordinate_labels(self, numbers=None, skip_first=True, font_size=24):
        if hasattr(self, "coordinate_labels") and len(self.coordinate_labels) > 0:
            self.remove(self.coordinate_labels)

        if numbers is None:
            numbers = self.get_default_coordinate_values(skip_first=skip_first)

        labels = VGroup()
        unit_size = self.get_unit_size()

        for number in numbers:
            z = complex(number)
            point = self.number_to_point(z)

            if abs(z.imag) < 1e-8:
                label_text = self._format_complex_label(z)
                label = Tex(label_text)
                label.set_height(max(0.18, 0.018 * font_size))
                label.next_to(point, DOWN, buff=0.15 * unit_size)
                label.semantic_type = "math_formula"
                label.semantic_role = "complex_axis_label"
                label.semantic_content = label_text
            else:
                label_text = self._format_complex_label(z)
                label = Tex(label_text)
                label.set_height(max(0.18, 0.018 * font_size))
                direction = RIGHT if z.imag > 0 else LEFT
                label.next_to(point, direction, buff=0.15 * unit_size)
                label.semantic_type = "math_formula"
                label.semantic_role = "imaginary_axis_label"
                label.semantic_content = label_text

            labels.add(label)

        self.coordinate_labels = labels
        self.add(labels)
        return self

    def get_bbox(self):
        return self.get_bounding_box()


def MathComplexPlane(**kwargs):
    plane = ComplexPlane(
        semantic_type="coordinate_system",
        semantic_role="math_complex_plane",
        semantic_content="complex plane",
        **kwargs
    )
    return plane


def UnitCircleComplexPlane(**kwargs):
    plane = ComplexPlane(
        semantic_type="coordinate_system",
        semantic_role="unit_circle_coordinate",
        semantic_content="|z| = 1",
        **kwargs
    )
    return plane


def PhasorComplexPlane(**kwargs):
    plane = ComplexPlane(
        semantic_type="coordinate_system",
        semantic_role="phasor_coordinate",
        semantic_content="z = a + bi",
        **kwargs
    )
    return plane