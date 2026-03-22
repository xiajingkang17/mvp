class CoordinateSystem(ABC):
    """
    Abstract class for Axes and NumberPlane
    """

    def __init__(self, x_range, y_range, num_sampled_graph_points_per_tick):
        pass

    @abstractmethod
    def coords_to_point(self) -> Vect3 | Vect3Array:
        pass

    @abstractmethod
    def point_to_coords(self, point) -> tuple[float | VectN, ...]:
        pass

    def c2p(self) -> Vect3 | Vect3Array:
        """
        Abbreviation for coords_to_point
        """

    def p2c(self, point) -> tuple[float | VectN, ...]:
        """
        Abbreviation for point_to_coords
        """

    def get_origin(self) -> Vect3:
        pass

    @abstractmethod
    def get_axes(self) -> VGroup:
        pass

    @abstractmethod
    def get_all_ranges(self) -> list[np.ndarray]:
        pass

    def get_axis(self, index) -> NumberLine:
        pass

    def get_x_axis(self) -> NumberLine:
        pass

    def get_y_axis(self) -> NumberLine:
        pass

    def get_z_axis(self) -> NumberLine:
        pass

    def get_x_axis_label(self, label_tex, edge, direction) -> Tex:
        pass

    def get_y_axis_label(self, label_tex, edge, direction) -> Tex:
        pass

    def get_axis_label(self, label_tex, axis, edge, direction, buff, ensure_on_screen) -> Tex:
        pass

    def get_axis_labels(self, x_label_tex, y_label_tex) -> VGroup:
        pass

    def get_line_from_axis_to_point(self, index, point, line_func, color, stroke_width) -> T:
        pass

    def get_v_line(self, point):
        pass

    def get_h_line(self, point):
        pass

    def get_graph(self, function, x_range, bind) -> ParametricCurve:
        pass

    def get_parametric_curve(self, function) -> ParametricCurve:
        pass

    def input_to_graph_point(self, x, graph) -> Vect3 | None:
        pass

    def i2gp(self, x, graph) -> Vect3 | None:
        """
        Alias for input_to_graph_point
        """

    def bind_graph_to_func(self, graph, func, jagged, get_discontinuities) -> VMobject:
        """
        Use for graphing functions which might change over time, or change with
        conditions
        """

    def get_graph_label(self, graph, label, x, direction, buff, color) -> Tex | Mobject:
        pass

    def get_v_line_to_graph(self, x, graph):
        pass

    def get_h_line_to_graph(self, x, graph):
        pass

    def get_scatterplot(self, x_values, y_values):
        pass

    def angle_of_tangent(self, x, graph, dx) -> float:
        pass

    def slope_of_tangent(self, x, graph) -> float:
        pass

    def get_tangent_line(self, x, graph, length, line_func) -> T:
        pass

    def get_riemann_rectangles(self, graph, x_range, dx, input_sample_type, stroke_width, stroke_color, fill_opacity, colors, negative_color, stroke_background, show_signed_area) -> VGroup:
        pass

    def get_area_under_graph(self, graph, x_range, fill_color, fill_opacity):
        pass