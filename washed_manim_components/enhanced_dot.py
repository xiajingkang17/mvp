class Dot(Circle):
    """
    Creates a dot. Dot is a filled white circle with no boundary and DEFAULT_DOT_RADIUS.
    Parameters
    -----
    point : array_like
        Coordinates of center of the dot.
    Examples :
            dot = Dot(point=(1, 2, 0))

    Returns
    -----
    out : Dot object
        A Dot object satisfying the specified parameters
    """

    def __init__(
        self,
        point=ORIGIN,
        radius=DEFAULT_DOT_RADIUS,
        stroke_color=WHITE,
        stroke_width=0,
        fill_opacity=1.0,
        fill_color=WHITE,
        **kwargs
    ):
        super().__init__(
            radius=radius,
            stroke_color=stroke_color,
            stroke_width=stroke_width,
            fill_opacity=fill_opacity,
            fill_color=fill_color,
            **kwargs
        )
        self.move_to(point)
        self.semantic_role = "point_marker"
        self.semantic_content = {
            "shape": "dot",
            "center": point,
            "radius": radius,
            "stroke_color": stroke_color,
            "stroke_width": stroke_width,
            "fill_opacity": fill_opacity,
            "fill_color": fill_color,
        }