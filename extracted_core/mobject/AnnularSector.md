================================================================================
Class: AnnularSector
Source: manimlib/mobject/geometry.py:516
================================================================================

Documentation:
----------------------------------------
Creates an annular sector.
Parameters
-----
inner_radius : float
    Inner radius of the annular sector
outer_radius : float
    Outer radius of the annular sector
start_angle : float
    Starting angle of the annular sector (Angles are measured counter-clockwise)
angle : float
    Angle subtended at the center of the annular sector (Angles are measured counter-clockwise)
arc_center : array_like
    Coordinates of center of the annular sector
Examples :
        annularSector = AnnularSector(inner_radius=1, outer_radius=2, angle=TAU/2, start_angle=TAU*3/4, arc_center=(1,-2,0))
Returns
-----
out : AnnularSector object
    An AnnularSector object satisfying the specified parameters

Inherits from:
  VMobject

Methods:
----------------------------------------

  Method: __init__
    def __init__(angle, start_angle, inner_radius, outer_radius, arc_center, fill_color, fill_opacity, stroke_width)
    Source line: 539
