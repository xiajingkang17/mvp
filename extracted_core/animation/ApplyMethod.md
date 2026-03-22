================================================================================
Class: ApplyMethod
Source: manimlib/animation/transform.py:161
================================================================================

Inherits from:
  Transform

Methods:
----------------------------------------

  Method: __init__
    def __init__(method)

      method is a method of Mobject, *args are arguments for
      that method.  Key word arguments should be passed in
      as the last arg, as a dict, since **kwargs is for
      configuration of the transform itself
      
      Relies on the fact that mobject methods return the mobject
    Source line: 162

  Method: check_validity_of_input
    def check_validity_of_input(method) -> None
    Source line: 176

  Method: create_target
    def create_target() -> Mobject
    Source line: 184
