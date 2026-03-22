from manimlib import *
import numpy as np
from abc import ABC, abstractmethod


class CoordinateSystem(VGroup, ABC):
    """
    Cleaned abstract base class for coordinate systems in ManimGL.
    Encapsulates shared coordinate conversion, graphing helpers, and semantic labels.
    """

    def __init__(
        self,
        x_range=(-8, 8, 1),
        y_range=(-4, 4, 1),
        num_sampled_graph_points_per_tick=5,
        semantic_type="coordinate_system",
        semantic_role="",
        semantic_content=None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.x_range = self._normalize_range(x_range)
        self.y_range = self._normalize_range(y_range)
        self.num_sampled_graph_points_per_tick = int(num_sampled_graph_points_per_tick)

        self._semantic_type = ""
        self._semantic_role = ""
        self._semantic_content = None
        self.semantic_type = semantic_type
        self.semantic_role = semantic_role
        self.semantic_content = semantic_content

    @staticmethod
    def _normalize_range(value):
        arr = np.array(value, dtype=float).reshape(-1)
        if len(arr) == 2:
            arr = np.array([arr[0], arr[1], 1.0])
        if len(arr) != 3:
            raise ValueError("Range must contain 2 or 3 numeric values.")
        if arr[2] == 0:
            raise ValueError("Range step cannot be zero.")
        return arr

    @property
    def semantic_type(self):
        return self._semantic_type

    @semantic_type.setter
    def semantic_type(self, value):
        if not isinstance(value, str):
            raise TypeError("semantic_type must be a string.")
        if not value.strip():
            raise ValueError("semantic_type cannot be empty.")
        self._semantic_type = value

    @property
    def semantic_role(self):
        return self._semantic_role

    @semantic_role.setter
    def semantic_role(self, value):
        if not isinstance(value, str):
            raise TypeError("semantic_role must be a string.")
        self._semantic_role = value

    @property
    def semantic_content(self):
        return self._semantic_content

    @semantic_content.setter
    def semantic_content(self, value):
        if value is not None and not isinstance(value, str):
            raise TypeError("semantic_content must be a string or None.")
        self._semantic_content = value

    def copy(self, **kwargs):
        new_obj = super().copy(**kwargs)
        new_obj._semantic_type = getattr(self, "_semantic_type", "")
        new_obj._semantic_role = getattr(self, "_semantic_role", "")
        new_obj._semantic_content = getattr(self, "_semantic_content", None)
        if hasattr(self, "x_range"):
            new_obj.x_range = np.array(self.x_range)
        if hasattr(self, "y_range"):
            new_obj.y_range = np.array(self.y_range)
        if hasattr(self, "num_sampled_graph_points_per_tick"):
            new_obj.num_sampled_graph_points_per_tick = self.num_sampled_graph_points_per_tick
        return new_obj

    def get_bbox(self):
        return np.array(self.get_bounding_box())

    @abstractmethod
    def coords_to_point(self, *coords):
        pass

    @abstractmethod
    def point_to_coords(self, point):
        pass

    def c2p(self, *coords):
        return self.coords_to_point(*coords)

    def p2c(self, point):
        return self.point_to_coords(point)

    def get_origin(self):
        zeros = [0] * len(self.get_all_ranges())
        return self.coords_to_point(*zeros)

    @abstractmethod
    def get_axes(self):
        pass

    @abstractmethod
    def get_all_ranges(self):
        pass

    def get_axis(self, index):
        axes = self.get_axes()
        if index < 0 or index >= len(axes):
            raise IndexError("Axis index out of range.")
        return axes[index]

    def get_x_axis(self):
        return self.get_axis(0)

    def get_y_axis(self):
        return self.get_axis(1)

    def get_z_axis(self):
        return self.get_axis(2)

    def get_x_axis_label(self, label_tex, edge=RIGHT, direction=DOWN, buff=SMALL_BUFF, ensure_on_screen=False):
        return self.get_axis_label(
            label_tex=label_tex,
            axis=self.get_x_axis(),
            edge=edge,
            direction=direction,
            buff=buff,
            ensure_on_screen=ensure_on_screen,
        )

    def get_y_axis_label(self, label_tex, edge=UP, direction=LEFT, buff=SMALL_BUFF, ensure_on_screen=False):
        return self.get_axis_label(
            label_tex=label_tex,
            axis=self.get_y_axis(),
            edge=edge,
            direction=direction,
            buff=buff,
            ensure_on_screen=ensure_on_screen,
        )

    def get_axis_label(
        self,
        label_tex,
        axis,
        edge,
        direction,
        buff=SMALL_BUFF,
        ensure_on_screen=False
    ):
        label = label_tex if isinstance(label_tex, Mobject) else Tex(str(label_tex))
        label.next_to(axis.get_edge_center(edge), direction, buff=buff)
        if ensure_on_screen:
            frame = FRAME_X_RADIUS * RIGHT + FRAME_Y_RADIUS * UP
            center = label.get_center()
            clipped = np.array([
                np.clip(center[0], -frame[0] + 0.3, frame[0] - 0.3),
                np.clip(center[1], -frame[1] + 0.3, frame[1] - 0.3),
                center[2],
            ])
            label.shift(clipped - center)
        return label

    def get_axis_labels(self, x_label_tex="x", y_label_tex="y"):
        labels = VGroup(
            self.get_x_axis_label(x_label_tex),
            self.get_y_axis_label(y_label_tex),
        )
        return labels

    def get_line_from_axis_to_point(
        self,
        index,
        point,
        line_func=DashedLine,
        color=GREY_A,
        stroke_width=2
    ):
        axis_point = self.get_axis(index).n2p(self.point_to_coords(point)[index])
        line = line_func(axis_point, point)
        line.set_stroke(color=color, width=stroke_width)
        return line

    def get_v_line(self, point):
        return self.get_line_from_axis_to_point(0, point)

    def get_h_line(self, point):
        return self.get_line_from_axis_to_point(1, point)

    def get_graph(self, function, x_range=None, bind=False, **kwargs):
        if x_range is None:
            x_range = self.x_range
        x_range = self._normalize_range(x_range)
        graph = self.get_parametric_curve(
            lambda t: self.coords_to_point(t, function(t)),
            t_range=x_range,
            **kwargs
        )
        graph.underlying_function = function
        graph.semantic_type = "function_curve" if hasattr(graph, "semantic_type") else None
        if bind:
            self.bind_graph_to_func(graph, function)
        return graph

    def get_parametric_curve(self, function, t_range=None, **kwargs):
        if t_range is None:
            t_range = self.x_range
        t_range = self._normalize_range(t_range)
        curve = ParametricCurve(
            function,
            t_range=t_range,
            **kwargs
        )
        return curve

    def input_to_graph_point(self, x, graph):
        if hasattr(graph, "underlying_function"):
            try:
                return self.coords_to_point(x, graph.underlying_function(x))
            except Exception:
                return None
        if hasattr(graph, "quick_point_from_proportion"):
            x_min, x_max = self.x_range[:2]
            alpha = inverse_interpolate(x_min, x_max, x)
            alpha = np.clip(alpha, 0, 1)
            return graph.quick_point_from_proportion(alpha)
        return None

    def i2gp(self, x, graph):
        return self.input_to_graph_point(x, graph)

    def bind_graph_to_func(
        self,
        graph,
        func,
        jagged=False,
        get_discontinuities=None
    ):
        graph.underlying_function = func

        def updater(mob):
            new_graph = self.get_graph(func, x_range=self.x_range)
            if jagged:
                new_graph.make_jagged()
            mob.set_points(new_graph.get_points())

        graph.add_updater(updater)
        return graph

    def get_graph_label(
        self,
        graph,
        label,
        x=None,
        direction=RIGHT,
        buff=SMALL_BUFF,
        color=None
    ):
        label_mob = label if isinstance(label, Mobject) else Tex(str(label))
        if color is None:
            color = graph.get_color()
        label_mob.set_color(color)

        if x is None:
            x = self.x_range[1]
        point = self.input_to_graph_point(x, graph)
        if point is None:
            point = graph.get_end()
        label_mob.next_to(point, direction, buff=buff)
        return label_mob

    def get_v_line_to_graph(self, x, graph, line_func=DashedLine, color=GREY_A, stroke_width=2):
        point = self.input_to_graph_point(x, graph)
        if point is None:
            return VGroup()
        return self.get_line_from_axis_to_point(0, point, line_func=line_func, color=color, stroke_width=stroke_width)

    def get_h_line_to_graph(self, x, graph, line_func=DashedLine, color=GREY_A, stroke_width=2):
        point = self.input_to_graph_point(x, graph)
        if point is None:
            return VGroup()
        return self.get_line_from_axis_to_point(1, point, line_func=line_func, color=color, stroke_width=stroke_width)

    def get_scatterplot(self, x_values, y_values, dot_radius=0.05, color=YELLOW):
        if len(x_values) != len(y_values):
            raise ValueError("x_values and y_values must have the same length.")
        dots = VGroup()
        for x, y in zip(x_values, y_values):
            dot = Dot(radius=dot_radius, color=color)
            dot.move_to(self.coords_to_point(x, y))
            dots.add(dot)
        return dots

    def angle_of_tangent(self, x, graph, dx=1e-6):
        p0 = self.input_to_graph_point(x, graph)
        p1 = self.input_to_graph_point(x + dx, graph)
        if p0 is None or p1 is None:
            raise ValueError("Cannot compute tangent angle for the given graph.")
        vect = p1 - p0
        return angle_of_vector(vect)

    def slope_of_tangent(self, x, graph, dx=1e-6):
        p0 = self.input_to_graph_point(x, graph)
        p1 = self.input_to_graph_point(x + dx, graph)
        if p0 is None or p1 is None:
            raise ValueError("Cannot compute tangent slope for the given graph.")
        coords0 = self.point_to_coords(p0)
        coords1 = self.point_to_coords(p1)
        denom = coords1[0] - coords0[0]
        if abs(denom) < 1e-12:
            return np.inf
        return (coords1[1] - coords0[1]) / denom

    def get_tangent_line(self, x, graph, length=5, line_func=Line):
        point = self.input_to_graph_point(x, graph)
        if point is None:
            raise ValueError("Cannot create tangent line for the given graph.")
        angle = self.angle_of_tangent(x, graph)
        line = line_func(LEFT, RIGHT)
        line.set_width(length)
        line.rotate(angle)
        line.move_to(point)
        return line

    def get_riemann_rectangles(
        self,
        graph,
        x_range=None,
        dx=0.1,
        input_sample_type="left",
        stroke_width=1,
        stroke_color=BLACK,
        fill_opacity=1,
        colors=(BLUE, GREEN),
        negative_color=RED,
        stroke_background=False,
        show_signed_area=True
    ):
        if x_range is None:
            x_range = self.x_range[:2]
        x_min, x_max = x_range[:2]
        rects = VGroup()
        xs = np.arange(x_min, x_max, dx)

        for x0 in xs:
            if input_sample_type == "left":
                sample_x = x0
            elif input_sample_type == "right":
                sample_x = min(x0 + dx, x_max)
            else:
                sample_x = x0 + 0.5 * dx

            point = self.input_to_graph_point(sample_x, graph)
            if point is None:
                continue

            y_val = self.point_to_coords(point)[1]
            x1 = min(x0 + dx, x_max)

            p1 = self.coords_to_point(x0, 0)
            p2 = self.coords_to_point(x1, 0)
            p3 = self.coords_to_point(x1, y_val)
            p4 = self.coords_to_point(x0, y_val)

            rect = Polygon(p1, p2, p3, p4)
            rect.set_stroke(color=stroke_color, width=stroke_width)
            if show_signed_area and y_val < 0:
                rect.set_fill(negative_color, opacity=fill_opacity)
            else:
                rect.set_fill(interpolate_color(colors[0], colors[1], inverse_interpolate(x_min, x_max, sample_x)), opacity=fill_opacity)
            if stroke_background:
                rect.set_flat_stroke(False)
            rects.add(rect)
        return rects

    def get_area_under_graph(
        self,
        graph,
        x_range=None,
        fill_color=BLUE,
        fill_opacity=0.5
    ):
        rects = self.get_riemann_rectangles(
            graph=graph,
            x_range=x_range,
            dx=0.02,
            stroke_width=0,
            fill_opacity=fill_opacity,
            colors=(fill_color, fill_color),
            negative_color=fill_color,
        )
        return rects


class DatasetCoordinateSystem(CoordinateSystem):
    """
    Concrete dataset-ready 2D coordinate system wrapper built from two NumberLine axes.
    """

    def __init__(
        self,
        x_range=(-8, 8, 1),
        y_range=(-4, 4, 1),
        axis_config=None,
        x_axis_config=None,
        y_axis_config=None,
        width=10,
        height=6,
        semantic_type="coordinate_system",
        semantic_role="generic_coordinate",
        semantic_content=None,
        **kwargs
    ):
        self.axis_config = dict(axis_config or {})
        self.x_axis_config = dict(x_axis_config or {})
        self.y_axis_config = dict(y_axis_config or {})
        self._width = float(width)
        self._height = float(height)

        super().__init__(
            x_range=x_range,
            y_range=y_range,
            semantic_type=semantic_type,
            semantic_role=semantic_role,
            semantic_content=semantic_content,
            **kwargs
        )

        self._init_axes()

    def _init_axes(self):
        x_axis_config = dict(self.axis_config)
        x_axis_config.update(self.x_axis_config)
        y_axis_config = dict(self.axis_config)
        y_axis_config.update(self.y_axis_config)

        self.x_axis = NumberLine(x_range=self.x_range, **x_axis_config)
        self.x_axis.set_width(self._width)

        self.y_axis = NumberLine(x_range=self.y_range, **y_axis_config)
        self.y_axis.set_height(self._height)
        self.y_axis.rotate(90 * DEGREES, about_point=ORIGIN)

        origin_shift = ORIGIN - self.x_axis.n2p(0)
        self.x_axis.shift(origin_shift)
        self.y_axis.shift(ORIGIN - self.y_axis.n2p(0))

        self.submobjects = []
        self.add(self.x_axis, self.y_axis)

    def copy(self, **kwargs):
        new_obj = super().copy(**kwargs)
        new_obj._semantic_type = getattr(self, "_semantic_type", "")
        new_obj._semantic_role = getattr(self, "_semantic_role", "")
        new_obj._semantic_content = getattr(self, "_semantic_content", None)
        return new_obj

    def get_axes(self):
        return VGroup(self.x_axis, self.y_axis)

    def get_all_ranges(self):
        return [np.array(self.x_range), np.array(self.y_range)]

    def coords_to_point(self, *coords):
        if len(coords) < 2:
            raise ValueError("coords_to_point expects at least 2 coordinates.")
        x, y = coords[:2]
        x_point = self.x_axis.n2p(x)
        y_point = self.y_axis.n2p(y)
        origin = self.get_origin()
        return x_point + y_point - origin

    def point_to_coords(self, point):
        x = self.x_axis.p2n(point)
        y = self.y_axis.p2n(point)
        return (x, y)


def KinematicsCoordinateSystem(**kwargs):
    return DatasetCoordinateSystem(
        semantic_type="coordinate_system",
        semantic_role="kinematics_coordinate",
        semantic_content="position-time or velocity-time",
        **kwargs
    )


def AnalyticGeometryCoordinateSystem(**kwargs):
    return DatasetCoordinateSystem(
        semantic_type="coordinate_system",
        semantic_role="analytic_geometry_coordinate",
        semantic_content="cartesian_plane",
        **kwargs
    )


def FunctionPlotCoordinateSystem(**kwargs):
    return DatasetCoordinateSystem(
        semantic_type="coordinate_system",
        semantic_role="function_plot_coordinate",
        semantic_content="y=f(x)",
        **kwargs
    )