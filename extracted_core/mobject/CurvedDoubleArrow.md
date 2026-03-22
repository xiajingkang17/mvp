================================================================================
Class: CurvedDoubleArrow
Source: manimlib/mobject/geometry.py:340
================================================================================

Documentation:
----------------------------------------
Creates a curved double arrow passing through the specified points with "angle" as the
angle subtended at its center.
Parameters
-----
start_point : array_like
    Starting point of the curved double arrow
end_point : array_like
    Ending point of the curved double arrow
angle : float
    Angle subtended by the curved double arrow at its center in radians. (Angles are measured counter-clockwise)
Examples :
        curvedDoubleArrow = CurvedDoubleArrow(start_point = (0, 0, 0), end_point = (1, 2, 0), angle = TAU/2)
        curvedDoubleArrow = CurvedDoubleArrow(start_point = (-2, 3, 0), end_point = (1, 2, 0), angle = -TAU/12, color = BLUE)
Returns
-----
out : CurvedDoubleArrow object
    A CurvedDoubleArrow object satisfying the specified parameters

Inherits from:
  CurvedArrow

Methods:
----------------------------------------

  Method: __init__
    def __init__(start_point, end_point)
    Source line: 361
