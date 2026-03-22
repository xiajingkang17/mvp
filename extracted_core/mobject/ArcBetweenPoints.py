class ArcBetweenPoints(Arc):
    """
    Creates an arc passing through the specified points with "angle" as the
    angle subtended at its center.
    Parameters
    -----
    start : array_like
        Starting point of the arc
    end : array_like
        Ending point of the arc
    angle : float
        Angle subtended by the arc at its center in radians. (Angles are measured counter-clockwise)
    Examples :
            arc = ArcBetweenPoints(start=(0, 0, 0), end=(1, 2, 0), angle=TAU / 2)
            arc = ArcBetweenPoints(start=(-2, 3, 0), end=(1, 2, 0), angle=-TAU / 12, color=BLUE)
    Returns
    -----
    out : ArcBetweenPoints object
        An ArcBetweenPoints object satisfying the specified parameters
    """

    def __init__(self, start, end, angle):
        pass