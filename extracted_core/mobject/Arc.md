================================================================================
Class: Arc
Source: manimlib/mobject/geometry.py:205
================================================================================

Documentation:
----------------------------------------
Creates an arc.
Parameters
-----
start_angle : float
    Starting angle of the arc in radians. (Angles are measured counter-clockwise)
angle : float
    Angle subtended by the arc at its center in radians. (Angles are measured counter-clockwise)
radius : float
    Radius of the arc
arc_center : array_like
    Center of the arc
Examples :
        arc = Arc(start_angle=TAU/4, angle=TAU/2, radius=3, arc_center=ORIGIN)
        arc = Arc(angle=TAU/4, radius=4.5, arc_center=(1,2,0), color=BLUE)
Returns
-----
out : Arc object
    An Arc object satisfying the specified parameters

Inherits from:
  TipableVMobject

Methods:
----------------------------------------

  Method: __init__
    def __init__(start_angle, angle, radius, n_components, arc_center)
    Source line: 227

  Method: get_arc_center
    def get_arc_center() -> Vect3

      Looks at the normals to the first two
      anchors, and finds their intersection points
    Source line: 247

  Method: get_start_angle
    def get_start_angle() -> float
    Source line: 262

  Method: get_stop_angle
    def get_stop_angle() -> float
    Source line: 266

  Method: move_arc_center_to
    def move_arc_center_to(point) -> Self
    Source line: 270
