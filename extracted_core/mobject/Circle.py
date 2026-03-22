class Circle(Arc):
    """
    Creates a circle.
    Parameters
    -----
    radius : float
        Radius of the circle
    arc_center : array_like
        Center of the circle
    Examples :
            circle = Circle(radius=2, arc_center=(1,2,0))
            circle = Circle(radius=3.14, arc_center=2 * LEFT + UP, color=DARK_BLUE)
    Returns
    -----
    out : Circle object
        A Circle object satisfying the specified parameters
    """

    def __init__(self, start_angle, stroke_color):
        pass

    def surround(self, mobject, dim_to_match, stretch, buff) -> Self:
        pass

    def point_at_angle(self, angle) -> Vect3:
        pass

    def get_radius(self) -> float:
        pass