================================================================================
Class: Axes
Source: manimlib/mobject/coordinate_systems.py:441
================================================================================

Inherits from:
  VGroup, CoordinateSystem

Methods:
----------------------------------------

  Method: __init__
    def __init__(x_range, y_range, axis_config, x_axis_config, y_axis_config, height, width, unit_size)
    Source line: 446

  Method: create_axis
    def create_axis(range_terms, axis_config, length) -> NumberLine
    Source line: 491

  Method: coords_to_point
    def coords_to_point() -> Vect3 | Vect3Array
    Source line: 501

  Method: point_to_coords
    def point_to_coords(point) -> tuple[float | VectN, ...]
    Source line: 508

  Method: get_axes
    def get_axes() -> VGroup
    Source line: 514

  Method: get_all_ranges
    def get_all_ranges() -> list[Sequence[float]]
    Source line: 517

  Method: add_coordinate_labels
    def add_coordinate_labels(x_values, y_values, excluding) -> VGroup
    Source line: 520
