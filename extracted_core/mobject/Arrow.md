================================================================================
Class: Arrow
Source: manimlib/mobject/geometry.py:1033
================================================================================

Documentation:
----------------------------------------
Creates an arrow.

Parameters
----------
start : array_like
    Starting point of the arrow
end : array_like
    Ending point of the arrow 
buff : float, optional
    Buffer distance from the start and end points. Default is MED_SMALL_BUFF.
path_arc : float, optional
    If set to a non-zero value, the arrow will be curved to subtend a circle by this angle.
    Default is 0 (straight arrow).
thickness : float, optional
    How wide should the base of the arrow be. This affects the shaft width. Default is 3.0.
tip_width_ratio : float, optional
    Ratio of the tip width to the shaft width. Default is 5.
tip_angle : float, optional
    Angle of the arrow tip in radians. Default is PI/3 (60 degrees).
max_tip_length_to_length_ratio : float, optional
    Maximum ratio of tip length to total arrow length. Prevents tips from being too large
    relative to the arrow. Default is 0.5.
max_width_to_length_ratio : float, optional
    Maximum ratio of arrow width to total arrow length. Prevents arrows from being too wide
    relative to their length. Default is 0.1.
**kwargs
    Additional keyword arguments passed to the parent Line class.

Examples
--------
>>> arrow = Arrow((0, 0, 0), (3, 0, 0))
>>> curved_arrow = Arrow(LEFT, RIGHT, path_arc=PI/4)
>>> thick_arrow = Arrow(UP, DOWN, thickness=5.0, tip_width_ratio=3)

Returns
-------
Arrow
    An Arrow object satisfying the specified parameters.

Inherits from:
  Line

Class Attributes:
----------------------------------------
  tickness_multiplier = 0.015

Methods:
----------------------------------------

  Method: __init__
    def __init__(start, end, buff, path_arc, fill_color, fill_opacity, stroke_width, thickness, tip_width_ratio, tip_angle, max_tip_length_to_length_ratio, max_width_to_length_ratio)
    Source line: 1077

  Method: get_key_dimensions
    def get_key_dimensions(length)
    Source line: 1108

  Method: set_points_by_ends
    def set_points_by_ends(start, end, buff, path_arc) -> Self
    Source line: 1123

  Method: get_start
    def get_start() -> Vect3
    Source line: 1188

  Method: get_end
    def get_end() -> Vect3
    Source line: 1192

  Method: get_start_and_end
    def get_start_and_end()
    Source line: 1195

  Method: put_start_and_end_on
    def put_start_and_end_on(start, end) -> Self
    Source line: 1198

  Method: scale
    def scale() -> Self
    Source line: 1202

  Method: set_thickness
    def set_thickness(thickness) -> Self
    Source line: 1207
