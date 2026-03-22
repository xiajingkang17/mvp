================================================================================
Class: DashedLine
Source: manimlib/mobject/geometry.py:808
================================================================================

Documentation:
----------------------------------------
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

Inherits from:
  Line

Methods:
----------------------------------------

  Method: __init__
    def __init__(start, end, dash_length, positive_space_ratio)
    Source line: 828

  Method: calculate_num_dashes
    def calculate_num_dashes(dash_length, positive_space_ratio) -> int
    Source line: 847

  Method: get_start
    def get_start() -> Vect3
    Source line: 854

  Method: get_end
    def get_end() -> Vect3
    Source line: 860

  Method: get_start_and_end
    def get_start_and_end() -> Tuple[Vect3, Vect3]
    Source line: 866

  Method: get_first_handle
    def get_first_handle() -> Vect3
    Source line: 869

  Method: get_last_handle
    def get_last_handle() -> Vect3
    Source line: 872
