class DashedLine(Line):
    """
    Creates a dashed line joining the points "start" and "end".
    Parameters
    -----
    start : array_like
        Starting point of the dashed line
    end : array_like
        Ending point of the dashed line
    dash_length : float
        length of each dash
    Examples :
            line = DashedLine((0, 0, 0), (3, 0, 0))
            line = DashedLine((1, 2, 3), (4, 5, 6), dash_length=0.01)
    Returns
    -----
    out : DashedLine object
        A DashedLine object satisfying the specified parameters
    """

    def __init__(self, start, end, dash_length, positive_space_ratio):
        pass

    def calculate_num_dashes(self, dash_length, positive_space_ratio) -> int:
        pass

    def get_start(self) -> Vect3:
        pass

    def get_end(self) -> Vect3:
        pass

    def get_start_and_end(self) -> Tuple[Vect3, Vect3]:
        pass

    def get_first_handle(self) -> Vect3:
        pass

    def get_last_handle(self) -> Vect3:
        pass