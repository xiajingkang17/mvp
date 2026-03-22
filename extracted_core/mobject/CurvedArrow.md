================================================================================
Class: CurvedArrow
Source: manimlib/mobject/geometry.py:309
================================================================================

Documentation:
----------------------------------------
Creates a curved arrow passing through the specified points with "angle" as the
angle subtended at its center.
Parameters
-----
start_point : array_like
    Starting point of the curved arrow
end_point : array_like
    Ending point of the curved arrow
angle : float
    Angle subtended by the curved arrow at its center in radians. (Angles are measured counter-clockwise)
Examples :
        curvedArrow = CurvedArrow(start_point=(0, 0, 0), end_point=(1, 2, 0), angle=TAU/2)
        curvedArrow = CurvedArrow(start_point=(-2, 3, 0), end_point=(1, 2, 0), angle=-TAU/12, color=BLUE)
Returns
-----
out : CurvedArrow object
    A CurvedArrow object satisfying the specified parameters

Inherits from:
  ArcBetweenPoints

Methods:
----------------------------------------

  Method: __init__
    def __init__(start_point, end_point)
    Source line: 330
