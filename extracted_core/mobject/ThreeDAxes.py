class ThreeDAxes(Axes):

    def __init__(self, x_range, y_range, z_range, z_axis_config, z_normal, depth):
        pass

    def get_all_ranges(self) -> list[Sequence[float]]:
        pass

    def add_axis_labels(self, x_tex, y_tex, z_tex, font_size, buff):
        pass

    def get_graph(self, func, color, opacity, u_range, v_range) -> ParametricSurface:
        pass

    def get_parametric_surface(self, func, color, opacity) -> ParametricSurface:
        pass