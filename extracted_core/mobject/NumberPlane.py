class NumberPlane(Axes):

    def __init__(self, x_range, y_range, background_line_style, faded_line_style, faded_line_ratio, make_smooth_after_applying_functions):
        pass

    def init_background_lines(self) -> None:
        pass

    def get_lines(self) -> tuple[VGroup, VGroup]:
        pass

    def get_lines_parallel_to_axis(self, axis1, axis2) -> tuple[VGroup, VGroup]:
        pass

    def get_x_unit_size(self) -> float:
        pass

    def get_y_unit_size(self) -> list:
        pass

    def get_axes(self) -> VGroup:
        pass

    def get_vector(self, coords) -> Arrow:
        pass

    def prepare_for_nonlinear_transform(self, num_inserted_curves) -> Self:
        pass