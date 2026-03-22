================================================================================
Class: ShowPartial
Source: manimlib/animation/creation.py:25
================================================================================

Documentation:
----------------------------------------
Abstract class for ShowCreation and ShowPassingFlash

Inherits from:
  Animation, ABC

Methods:
----------------------------------------

  Method: __init__
    def __init__(mobject, should_match_start)
    Source line: 29

  Method: interpolate_submobject
    def interpolate_submobject(submob, start_submob, alpha) -> None
    Source line: 33

  Method: get_bounds
    Decorators: abstractmethod
    def get_bounds(alpha) -> tuple[float, float]
    Source line: 44
