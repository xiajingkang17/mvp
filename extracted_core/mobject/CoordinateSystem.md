================================================================================
Class: CoordinateSystem
Source: manimlib/mobject/coordinate_systems.py:54
================================================================================

Documentation:
----------------------------------------
Abstract class for Axes and NumberPlane

Inherits from:
  ABC

Methods:
----------------------------------------

  Method: __init__
    def __init__(x_range, y_range, num_sampled_graph_points_per_tick)
    Source line: 60

  Method: coords_to_point
    Decorators: abstractmethod
    def coords_to_point() -> Vect3 | Vect3Array
    Source line: 71

  Method: point_to_coords
    Decorators: abstractmethod
    def point_to_coords(point) -> tuple[float | VectN, ...]
    Source line: 75

  Method: c2p
    def c2p() -> Vect3 | Vect3Array

      Abbreviation for coords_to_point
    Source line: 78

  Method: p2c
    def p2c(point) -> tuple[float | VectN, ...]

      Abbreviation for point_to_coords
    Source line: 82

  Method: get_origin
    def get_origin() -> Vect3
    Source line: 86

  Method: get_axes
    Decorators: abstractmethod
    def get_axes() -> VGroup
    Source line: 90

  Method: get_all_ranges
    Decorators: abstractmethod
    def get_all_ranges() -> list[np.ndarray]
    Source line: 94

  Method: get_axis
    def get_axis(index) -> NumberLine
    Source line: 97

  Method: get_x_axis
    def get_x_axis() -> NumberLine
    Source line: 100

  Method: get_y_axis
    def get_y_axis() -> NumberLine
    Source line: 103

  Method: get_z_axis
    def get_z_axis() -> NumberLine
    Source line: 106

  Method: get_x_axis_label
    def get_x_axis_label(label_tex, edge, direction) -> Tex
    Source line: 109

  Method: get_y_axis_label
    def get_y_axis_label(label_tex, edge, direction) -> Tex
    Source line: 121

  Method: get_axis_label
    def get_axis_label(label_tex, axis, edge, direction, buff, ensure_on_screen) -> Tex
    Source line: 133

  Method: get_axis_labels
    def get_axis_labels(x_label_tex, y_label_tex) -> VGroup
    Source line: 152

  Method: get_line_from_axis_to_point
    def get_line_from_axis_to_point(index, point, line_func, color, stroke_width) -> T
    Source line: 164

  Method: get_v_line
    def get_v_line(point)
    Source line: 177

  Method: get_h_line
    def get_h_line(point)
    Source line: 180

  Method: get_graph
    def get_graph(function, x_range, bind) -> ParametricCurve
    Source line: 184

  Method: get_parametric_curve
    def get_parametric_curve(function) -> ParametricCurve
    Source line: 215

  Method: input_to_graph_point
    def input_to_graph_point(x, graph) -> Vect3 | None
    Source line: 228

  Method: i2gp
    def i2gp(x, graph) -> Vect3 | None

      Alias for input_to_graph_point
    Source line: 249

  Method: bind_graph_to_func
    def bind_graph_to_func(graph, func, jagged, get_discontinuities) -> VMobject

      Use for graphing functions which might change over time, or change with
      conditions
    Source line: 255

  Method: get_graph_label
    def get_graph_label(graph, label, x, direction, buff, color) -> Tex | Mobject
    Source line: 284

  Method: get_v_line_to_graph
    def get_v_line_to_graph(x, graph)
    Source line: 319

  Method: get_h_line_to_graph
    def get_h_line_to_graph(x, graph)
    Source line: 322

  Method: get_scatterplot
    def get_scatterplot(x_values, y_values)
    Source line: 325

  Method: angle_of_tangent
    def angle_of_tangent(x, graph, dx) -> float
    Source line: 332

  Method: slope_of_tangent
    def slope_of_tangent(x, graph) -> float
    Source line: 342

  Method: get_tangent_line
    def get_tangent_line(x, graph, length, line_func) -> T
    Source line: 350

  Method: get_riemann_rectangles
    def get_riemann_rectangles(graph, x_range, dx, input_sample_type, stroke_width, stroke_color, fill_opacity, colors, negative_color, stroke_background, show_signed_area) -> VGroup
    Source line: 363

  Method: get_area_under_graph
    def get_area_under_graph(graph, x_range, fill_color, fill_opacity)
    Source line: 417
