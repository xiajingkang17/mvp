class Sector(AnnularSector):
    """
    Creates a sector.
    Parameters
    -----
    outer_radius : float
        Radius of the sector
    start_angle : float
        Starting angle of the sector in radians. (Angles are measured counter-clockwise)
    angle : float
        Angle subtended by the sector at its center in radians. (Angles are measured counter-clockwise)
    arc_center : array_like
        Coordinates of center of the sector
    Examples :
            sector = Sector(outer_radius=1, start_angle=TAU/3, angle=TAU/2, arc_center=[0,3,0])
            sector = Sector(outer_radius=3, start_angle=TAU/4, angle=TAU/4, arc_center=ORIGIN, color=PINK)
    Returns
    -----
    out : Sector object
        An Sector object satisfying the specified parameters
    """

    def __init__(self, angle, radius):
        pass