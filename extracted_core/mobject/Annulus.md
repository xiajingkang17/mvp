================================================================================
Class: Annulus
Source: manimlib/mobject/geometry.py:610
================================================================================

Documentation:
----------------------------------------
Creates an annulus.
Parameters
-----
inner_radius : float
    Inner radius of the annulus
outer_radius : float
    Outer radius of the annulus
arc_center : array_like
    Coordinates of center of the annulus
Examples :
        annulus = Annulus(inner_radius=2, outer_radius=3, arc_center=(1, -1, 0))
        annulus = Annulus(inner_radius=2, outer_radius=3, stroke_width=20, stroke_color=RED, fill_color=BLUE, arc_center=ORIGIN)
Returns
-----
out : Annulus object
    An Annulus object satisfying the specified parameters

Inherits from:
  VMobject

Methods:
----------------------------------------

  Method: __init__
    def __init__(inner_radius, outer_radius, fill_opacity, stroke_width, fill_color, center)
    Source line: 630
