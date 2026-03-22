================================================================================
Class: Circle
Source: manimlib/mobject/geometry.py:371
================================================================================

Documentation:
----------------------------------------
Creates a circle.
Parameters
-----
radius : float
    Radius of the circle
arc_center : array_like
    Center of the circle
Examples :
        circle = Circle(radius=2, arc_center=(1,2,0))
        circle = Circle(radius=3.14, arc_center=2 * LEFT + UP, color=DARK_BLUE)
Returns
-----
out : Circle object
    A Circle object satisfying the specified parameters

Inherits from:
  Arc

Methods:
----------------------------------------

  Method: __init__
    def __init__(start_angle, stroke_color)
    Source line: 389

  Method: surround
    def surround(mobject, dim_to_match, stretch, buff) -> Self
    Source line: 401

  Method: point_at_angle
    def point_at_angle(angle) -> Vect3
    Source line: 413

  Method: get_radius
    def get_radius() -> float
    Source line: 419
