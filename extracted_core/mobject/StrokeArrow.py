class StrokeArrow(Line):

    def __init__(self, start, end, stroke_color, stroke_width, buff, tip_width_ratio, tip_len_to_width, max_tip_length_to_length_ratio, max_width_to_length_ratio):
        pass

    def set_points_by_ends(self, start, end, buff, path_arc) -> Self:
        pass

    def insert_tip_anchor(self) -> Self:
        pass

    @Mobject.affects_data
    def create_tip_with_stroke_width(self) -> Self:
        pass

    def reset_tip(self) -> Self:
        pass

    def set_stroke(self, color, width) -> Self:
        pass

    def _handle_scale_side_effects(self, scale_factor) -> Self:
        pass