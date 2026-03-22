================================================================================
Class: Line
Source: manimlib/mobject/geometry.py:655
================================================================================

Documentation:
----------------------------------------
Creates a line joining the points "start" and "end".
Parameters
-----
start : array_like
    Starting point of the line
end : array_like
    Ending point of the line
Examples :
        line = Line((0, 0, 0), (3, 0, 0))
        line = Line((1, 2, 0), (-2, -3, 0), color=BLUE)
Returns
-----
out : Line object
    A Line object satisfying the specified parameters

Inherits from:
  TipableVMobject

Methods:
----------------------------------------

  Method: __init__
    def __init__(start, end, buff, path_arc)
    Source line: 673

  Method: set_points_by_ends
    def set_points_by_ends(start, end, buff, path_arc) -> Self
    Source line: 687

  Method: reset_points_around_ends
    def reset_points_around_ends() -> Self
    Source line: 705

  Method: set_path_arc
    def set_path_arc(path_arc) -> Self
    Source line: 713

  Method: set_start_and_end_attrs
    def set_start_and_end_attrs(start, end)
    Source line: 718

  Method: pointify
    def pointify(mob_or_point, direction) -> Vect3

      Take an argument passed into Line (or subclass) and turn
      it into a 3d point.
    Source line: 730

  Method: put_start_and_end_on
    def put_start_and_end_on(start, end) -> Self
    Source line: 751

  Method: get_vector
    def get_vector() -> Vect3
    Source line: 759

  Method: get_unit_vector
    def get_unit_vector() -> Vect3
    Source line: 762

  Method: get_angle
    def get_angle() -> float
    Source line: 765

  Method: get_projection
    def get_projection(point) -> Vect3

      Return projection of a point onto the line
    Source line: 768

  Method: get_slope
    def get_slope() -> float
    Source line: 776

  Method: set_angle
    def set_angle(angle, about_point) -> Self
    Source line: 779

  Method: set_length
    def set_length(length)
    Source line: 788

  Method: get_arc_length
    def get_arc_length() -> float
    Source line: 792

  Method: set_perpendicular_to_camera
    def set_perpendicular_to_camera(camera_frame)
    Source line: 798
