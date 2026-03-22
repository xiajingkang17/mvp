================================================================================
Class: Transform
Source: manimlib/animation/transform.py:24
================================================================================

Inherits from:
  Animation

Methods:
----------------------------------------

  Method: __init__
    def __init__(mobject, target_mobject, path_arc, path_arc_axis, path_func)
    Source line: 27

  Method: init_path_func
    def init_path_func() -> None
    Source line: 43

  Method: begin
    def begin() -> None
    Source line: 54

  Method: finish
    def finish() -> None
    Source line: 74

  Method: create_target
    def create_target() -> Mobject
    Source line: 78

  Method: check_target_mobject_validity
    def check_target_mobject_validity() -> None
    Source line: 83

  Method: clean_up_from_scene
    def clean_up_from_scene(scene) -> None
    Source line: 89

  Method: update_config
    def update_config() -> None
    Source line: 95

  Method: get_all_mobjects
    def get_all_mobjects() -> list[Mobject]
    Source line: 103

  Method: get_all_families_zipped
    def get_all_families_zipped() -> zip[tuple[Mobject]]
    Source line: 111

  Method: interpolate_submobject
    def interpolate_submobject(submob, start, target_copy, alpha)
    Source line: 121
