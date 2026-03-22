from manimlib import *


class SemanticMixin(object):
    def __init__(
        self,
        semantic_type="",
        semantic_role="",
        semantic_content=None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self._semantic_type = ""
        self._semantic_role = ""
        self._semantic_content = None
        self.semantic_type = semantic_type
        self.semantic_role = semantic_role
        self.semantic_content = semantic_content

    @property
    def semantic_type(self):
        return self._semantic_type

    @semantic_type.setter
    def semantic_type(self, value):
        if not isinstance(value, str):
            raise TypeError("semantic_type must be a string")
        self._semantic_type = value

    @property
    def semantic_role(self):
        return self._semantic_role

    @semantic_role.setter
    def semantic_role(self, value):
        if not isinstance(value, str):
            raise TypeError("semantic_role must be a string")
        self._semantic_role = value

    @property
    def semantic_content(self):
        return self._semantic_content

    @semantic_content.setter
    def semantic_content(self, value):
        if value is not None and not isinstance(value, str):
            raise TypeError("semantic_content must be a string or None")
        self._semantic_content = value


class Transform(SemanticMixin, Animation):
    CONFIG = {
        "path_arc": 0,
        "path_arc_axis": OUT,
        "path_func": None,
        "replace_mobject_with_target_in_scene": False,
        "semantic_type": "animation_transform",
        "semantic_role": "object_transform",
        "semantic_content": None,
    }

    def __init__(
        self,
        mobject,
        target_mobject=None,
        path_arc=0,
        path_arc_axis=OUT,
        path_func=None,
        semantic_type="animation_transform",
        semantic_role="object_transform",
        semantic_content=None,
        **kwargs
    ):
        if mobject is None:
            raise ValueError("mobject cannot be None")
        if not isinstance(mobject, Mobject):
            raise TypeError("mobject must be an instance of Mobject")

        self.target_mobject = target_mobject
        self.target_copy = None
        self.path_arc = path_arc
        self.path_arc_axis = path_arc_axis
        self.path_func = path_func

        super().__init__(
            mobject,
            path_arc=path_arc,
            path_arc_axis=path_arc_axis,
            path_func=path_func,
            semantic_type=semantic_type,
            semantic_role=semantic_role,
            semantic_content=semantic_content,
            **kwargs
        )
        self.init_path_func()
        self.check_target_mobject_validity()

    def init_path_func(self):
        if self.path_func is not None:
            return self
        if abs(self.path_arc) > 0:
            self.path_func = path_along_arc(
                self.path_arc,
                self.path_arc_axis,
            )
        else:
            self.path_func = straight_path
        return self

    def begin(self):
        self.target_mobject = self.create_target()
        self.check_target_mobject_validity()
        self.target_copy = self.target_mobject.copy()
        self.mobject.save_state()
        if hasattr(super(), "begin"):
            super().begin()
        return self

    def finish(self):
        if hasattr(super(), "finish"):
            super().finish()
        if self.target_mobject is not None:
            self.mobject.become(self.target_mobject)
        return self

    def create_target(self):
        if self.target_mobject is None:
            raise ValueError("target_mobject cannot be None")
        return self.target_mobject

    def check_target_mobject_validity(self):
        if self.target_mobject is None:
            return
        if not isinstance(self.target_mobject, Mobject):
            raise TypeError("target_mobject must be an instance of Mobject")

    def clean_up_from_scene(self, scene):
        if hasattr(super(), "clean_up_from_scene"):
            super().clean_up_from_scene(scene)
        if getattr(self, "replace_mobject_with_target_in_scene", False):
            scene.remove(self.mobject)
            if self.target_mobject is not None:
                scene.add(self.target_mobject)
        return self

    def update_config(self):
        self.init_path_func()
        return self

    def get_all_mobjects(self):
        mobs = [self.mobject]
        if self.starting_mobject is not None:
            mobs.append(self.starting_mobject)
        if self.target_copy is not None:
            mobs.append(self.target_copy)
        return mobs

    def get_all_families_zipped(self):
        return zip(*[
            mob.family_members_with_points()
            for mob in self.get_all_mobjects()
        ])

    def interpolate_submobject(self, submob, start, target_copy, alpha):
        submob.interpolate(start, target_copy, alpha, self.path_func)
        return submob

    def copy(self, **kwargs):
        new_obj = super().copy(**kwargs)
        new_obj._semantic_type = getattr(self, "_semantic_type", "")
        new_obj._semantic_role = getattr(self, "_semantic_role", "")
        new_obj._semantic_content = getattr(self, "_semantic_content", None)
        return new_obj


def ReplacementTransform(
    mobject,
    target_mobject,
    semantic_content=None,
    **kwargs
):
    return Transform(
        mobject,
        target_mobject,
        replace_mobject_with_target_in_scene=True,
        semantic_type="animation_transform",
        semantic_role="replacement_transform",
        semantic_content=semantic_content,
        **kwargs
    )


def PhysicsStateTransform(
    mobject,
    target_mobject,
    semantic_content=None,
    **kwargs
):
    return Transform(
        mobject,
        target_mobject,
        semantic_type="animation_transform",
        semantic_role="physics_state_transition",
        semantic_content=semantic_content,
        **kwargs
    )


def MathExpressionTransform(
    mobject,
    target_mobject,
    semantic_content=None,
    **kwargs
):
    return Transform(
        mobject,
        target_mobject,
        semantic_type="animation_transform",
        semantic_role="math_expression_transform",
        semantic_content=semantic_content,
        **kwargs
    )