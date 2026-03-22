================================================================================
Class: Ellipse
Source: manimlib/mobject/geometry.py:485
================================================================================

Documentation:
----------------------------------------
Creates an ellipse.
Parameters
-----
width : float
    Width of the ellipse
height : float
    Height of the ellipse
arc_center : array_like
    Coordinates of center of the ellipse
Examples :
        ellipse = Ellipse(width=4, height=1, arc_center=(3, 3, 0))
        ellipse = Ellipse(width=2, height=5, arc_center=ORIGIN, color=BLUE)
Returns
-----
out : Ellipse object
    An Ellipse object satisfying the specified parameters

Inherits from:
  Circle

Methods:
----------------------------------------

  Method: __init__
    def __init__(width, height)
    Source line: 505
