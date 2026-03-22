================================================================================
Class: CubicBezier
Source: manimlib/mobject/geometry.py:1239
================================================================================

Documentation:
----------------------------------------
Creates a cubic Bézier curve.

A cubic Bézier curve is defined by four control points: two anchor points (start and end)
and two handle points that control the curvature. The curve starts at the first anchor
point, is "pulled" toward the handle points, and ends at the second anchor point.

Parameters
----------
a0 : array_like
    First anchor point (starting point of the curve).
h0 : array_like
    First handle point (controls the initial direction and curvature from a0).
h1 : array_like
    Second handle point (controls the final direction and curvature toward a1).
a1 : array_like
    Second anchor point (ending point of the curve).
**kwargs
    Additional keyword arguments passed to the parent VMobject class, such as
    stroke_color, stroke_width, fill_color, fill_opacity, etc.
Returns
-------
CubicBezier
    A CubicBezier object representing the specified cubic Bézier curve.

Inherits from:
  VMobject

Methods:
----------------------------------------

  Method: __init__
    def __init__(a0, h0, h1, a1)
    Source line: 1267
