class VectorField(VMobject):

    def __init__(self, func, coordinate_system, sample_coords, density, magnitude_range, color, color_map_name, color_map, stroke_opacity, stroke_width, tip_width_ratio, tip_len_to_width, max_vect_len, max_vect_len_to_step_size, flat_stroke, norm_to_opacity_func):
        pass

    def init_points(self):
        pass

    def get_sample_points(self, center, width, height, depth, x_density, y_density, z_density) -> np.ndarray:
        pass

    def init_base_stroke_width_array(self, n_sample_points):
        pass

    def set_sample_coords(self, sample_coords):
        pass

    def set_stroke(self, color, width, opacity, behind, flat, recurse):
        pass

    def set_stroke_width(self, width):
        pass

    def update_sample_points(self):
        pass

    def update_vectors(self):
        pass