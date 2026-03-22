================================================================================
Class: StrokeArrow
Source: manimlib/mobject/geometry.py:940
================================================================================

Inherits from:
  Line

Methods:
----------------------------------------

  Method: __init__
    def __init__(start, end, stroke_color, stroke_width, buff, tip_width_ratio, tip_len_to_width, max_tip_length_to_length_ratio, max_width_to_length_ratio)
    Source line: 941

  Method: set_points_by_ends
    def set_points_by_ends(start, end, buff, path_arc) -> Self
    Source line: 968

  Method: insert_tip_anchor
    def insert_tip_anchor() -> Self
    Source line: 980

  Method: create_tip_with_stroke_width
    Decorators: Mobject.affects_data
    def create_tip_with_stroke_width() -> Self
    Source line: 996

  Method: reset_tip
    def reset_tip() -> Self
    Source line: 1008

  Method: set_stroke
    def set_stroke(color, width) -> Self
    Source line: 1015

  Method: _handle_scale_side_effects
    def _handle_scale_side_effects(scale_factor) -> Self
    Source line: 1027
