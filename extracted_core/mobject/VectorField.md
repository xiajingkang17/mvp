================================================================================
Class: VectorField
Source: manimlib/mobject/vector_field.py:141
================================================================================

Inherits from:
  VMobject

Methods:
----------------------------------------

  Method: __init__
    def __init__(func, coordinate_system, sample_coords, density, magnitude_range, color, color_map_name, color_map, stroke_opacity, stroke_width, tip_width_ratio, tip_len_to_width, max_vect_len, max_vect_len_to_step_size, flat_stroke, norm_to_opacity_func)
    Source line: 142

  Method: init_points
    def init_points()
    Source line: 206

  Method: get_sample_points
    def get_sample_points(center, width, height, depth, x_density, y_density, z_density) -> np.ndarray
    Source line: 211

  Method: init_base_stroke_width_array
    def init_base_stroke_width_array(n_sample_points)
    Source line: 231

  Method: set_sample_coords
    def set_sample_coords(sample_coords)
    Source line: 239

  Method: set_stroke
    def set_stroke(color, width, opacity, behind, flat, recurse)
    Source line: 243

  Method: set_stroke_width
    def set_stroke_width(width)
    Source line: 249

  Method: update_sample_points
    def update_sample_points()
    Source line: 255

  Method: update_vectors
    def update_vectors()
    Source line: 258
