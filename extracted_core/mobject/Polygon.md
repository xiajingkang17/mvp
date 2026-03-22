================================================================================
Class: Polygon
Source: manimlib/mobject/geometry.py:1279
================================================================================

Documentation:
----------------------------------------
Creates a polygon by joining the specified vertices.
Parameters
-----
*vertices : array_like
    Vertex of the polygon
Examples :
        triangle = Polygon((-3,0,0), (3,0,0), (0,3,0))
Returns
-----
out : Polygon object
    A Polygon object satisfying the specified parameters

Inherits from:
  VMobject

Methods:
----------------------------------------

  Method: __init__
    def __init__()
    Source line: 1294

  Method: get_vertices
    def get_vertices() -> Vect3Array
    Source line: 1302

  Method: round_corners
    def round_corners(radius) -> Self
    Source line: 1305
