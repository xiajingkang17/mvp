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

    def __init__(
        self,
        radius=1.0,
        color=RED,
        **kwargs
    ):
        super().__init__(
            start_angle=0,
            angle=TAU,
            radius=radius,
            color=color,
            **kwargs
        )
        self.semantic_role = "geometric_shape"
        self.semantic_content = f"circle(radius={radius}, center={self.get_center().tolist()})"

    def surround(self, mobject, dim_to_match=0, stretch=False, buff=MED_SMALL_BUFF) -> Self:
        self.replace(mobject, dim_to_match, stretch)
        self.scale(1 + buff / self.get_radius())
        self.semantic_role = "geometric_shape"
        self.semantic_content = (
            f"circle(radius={self.get_radius()}, center={self.get_center().tolist()}, "
            f"surrounds={mobject.__class__.__name__})"
        )
        return self

    def point_at_angle(self, angle) -> Vect3:
        start_angle = angle_of_vector(
            self.points[0] - self.get_center()
        )
        return self.point_from_proportion(
            (angle - start_angle) / TAU
        )

    def get_radius(self) -> float:
        return np.linalg.norm(self.get_start() - self.get_center())