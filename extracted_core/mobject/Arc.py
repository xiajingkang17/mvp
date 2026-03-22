class Arc(TipableVMobject):
    """
    Creates an arc.
    Parameters
    -----
    start_angle : float
        Starting angle of the arc in radians. (Angles are measured counter-clockwise)
    angle : float
        Angle subtended by the arc at its center in radians. (Angles are measured counter-clockwise)
    radius : float
        Radius of the arc
    arc_center : array_like
        Center of the arc
    Examples :
            arc = Arc(start_angle=TAU/4, angle=TAU/2, radius=3, arc_center=ORIGIN)
            arc = Arc(angle=TAU/4, radius=4.5, arc_center=(1,2,0), color=BLUE)
    Returns
    -----
    out : Arc object
        An Arc object satisfying the specified parameters
    """

    def __init__(self, start_angle, angle, radius, n_components, arc_center):
        pass

    def get_arc_center(self) -> Vect3:
        """
        Looks at the normals to the first two
        anchors, and finds their intersection points
        """

    def get_start_angle(self) -> float:
        pass

    def get_stop_angle(self) -> float:
        pass

    def move_arc_center_to(self, point) -> Self:
        pass