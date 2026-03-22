class Line(TipableVMobject):
    """
    Creates a line joining the points "start" and "end".
    Parameters
    -----
    start : array_like
        Starting point of the line
    end : array_like
        Ending point of the line
    Examples :
            line = Line((0, 0, 0), (3, 0, 0))
            line = Line((1, 2, 0), (-2, -3, 0), color=BLUE)
    Returns
    -----
    out : Line object
        A Line object satisfying the specified parameters
    """

    def __init__(self, start, end, buff, path_arc):
        pass

    def set_points_by_ends(self, start, end, buff, path_arc) -> Self:
        pass

    def reset_points_around_ends(self) -> Self:
        pass

    def set_path_arc(self, path_arc) -> Self:
        pass

    def set_start_and_end_attrs(self, start, end):
        pass

    def pointify(self, mob_or_point, direction) -> Vect3:
        """
        Take an argument passed into Line (or subclass) and turn
        it into a 3d point.
        """

    def put_start_and_end_on(self, start, end) -> Self:
        pass

    def get_vector(self) -> Vect3:
        pass

    def get_unit_vector(self) -> Vect3:
        pass

    def get_angle(self) -> float:
        pass

    def get_projection(self, point) -> Vect3:
        """
        Return projection of a point onto the line
        """

    def get_slope(self) -> float:
        pass

    def set_angle(self, angle, about_point) -> Self:
        pass

    def set_length(self, length):
        pass

    def get_arc_length(self) -> float:
        pass

    def set_perpendicular_to_camera(self, camera_frame):
        pass