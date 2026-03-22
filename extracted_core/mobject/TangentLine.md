================================================================================
Class: TangentLine
Source: manimlib/mobject/geometry.py:876
================================================================================

Documentation:
----------------------------------------
Creates a tangent line to the specified vectorized math object.
Parameters
-----
vmob : VMobject object
    Vectorized math object which the line will be tangent to
alpha : float
    Point on the perimeter of the vectorized math object. It takes value between 0 and 1
    both inclusive.
length : float
    Length of the tangent line
Examples :
        circle = Circle(arc_center=ORIGIN, radius=3, color=GREEN)
        tangentLine = TangentLine(vmob=circle, alpha=1/3, length=6, color=BLUE)
Returns
-----
out : TangentLine object
    A TangentLine object satisfying the specified parameters

Inherits from:
  Line

Methods:
----------------------------------------

  Method: __init__
    def __init__(vmob, alpha, length, d_alpha)
    Source line: 897
