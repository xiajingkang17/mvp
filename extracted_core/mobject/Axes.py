class Axes(VGroup, CoordinateSystem):

    def __init__(self, x_range, y_range, axis_config, x_axis_config, y_axis_config, height, width, unit_size):
        pass

    def create_axis(self, range_terms, axis_config, length) -> NumberLine:
        pass

    def coords_to_point(self) -> Vect3 | Vect3Array:
        pass

    def point_to_coords(self, point) -> tuple[float | VectN, ...]:
        pass

    def get_axes(self) -> VGroup:
        pass

    def get_all_ranges(self) -> list[Sequence[float]]:
        pass

    def add_coordinate_labels(self, x_values, y_values, excluding) -> VGroup:
        pass