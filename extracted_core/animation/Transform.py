class Transform(Animation):

    def __init__(self, mobject, target_mobject, path_arc, path_arc_axis, path_func):
        pass

    def init_path_func(self) -> None:
        pass

    def begin(self) -> None:
        pass

    def finish(self) -> None:
        pass

    def create_target(self) -> Mobject:
        pass

    def check_target_mobject_validity(self) -> None:
        pass

    def clean_up_from_scene(self, scene) -> None:
        pass

    def update_config(self) -> None:
        pass

    def get_all_mobjects(self) -> list[Mobject]:
        pass

    def get_all_families_zipped(self) -> zip[tuple[Mobject]]:
        pass

    def interpolate_submobject(self, submob, start, target_copy, alpha):
        pass