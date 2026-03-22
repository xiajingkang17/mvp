class RegularPolygon(Polygon):
    """
    Creates a regular polygon of edge length 1 at the center of the screen.
    Parameters
    -----
    n : int
        Number of vertices of the regular polygon
    start_angle : float
        Starting angle of the regular polygon in radians. (Angles are measured counter-clockwise)
    Examples :
            pentagon = RegularPolygon(n=5, start_angle=30 * DEGREES)
    Returns
    -----
    out : RegularPolygon object
        A RegularPolygon object satisfying the specified parameters
    """

    def __init__(self, n, radius, start_angle):
        pass