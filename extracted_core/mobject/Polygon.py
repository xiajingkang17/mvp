class Polygon(VMobject):
    """
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
    """

    def __init__(self):
        pass

    def get_vertices(self) -> Vect3Array:
        pass

    def round_corners(self, radius) -> Self:
        pass