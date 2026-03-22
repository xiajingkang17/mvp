================================================================================
Class: NumberPlane
Source: manimlib/mobject/coordinate_systems.py:624
================================================================================

Inherits from:
  Axes

Methods:
----------------------------------------

  Method: __init__
    def __init__(x_range, y_range, background_line_style, faded_line_style, faded_line_ratio, make_smooth_after_applying_functions)
    Source line: 637

  Method: init_background_lines
    def init_background_lines() -> None
    Source line: 662

  Method: get_lines
    def get_lines() -> tuple[VGroup, VGroup]
    Source line: 674

  Method: get_lines_parallel_to_axis
    def get_lines_parallel_to_axis(axis1, axis2) -> tuple[VGroup, VGroup]
    Source line: 684

  Method: get_x_unit_size
    def get_x_unit_size() -> float
    Source line: 709

  Method: get_y_unit_size
    def get_y_unit_size() -> list
    Source line: 712

  Method: get_axes
    def get_axes() -> VGroup
    Source line: 715

  Method: get_vector
    def get_vector(coords) -> Arrow
    Source line: 718

  Method: prepare_for_nonlinear_transform
    def prepare_for_nonlinear_transform(num_inserted_curves) -> Self
    Source line: 722
