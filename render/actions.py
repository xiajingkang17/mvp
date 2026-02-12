from __future__ import annotations

from dataclasses import dataclass

from schema.scene_plan_models import PlayAction, WaitAction
from render.motions import run_pin_to_corner


@dataclass(frozen=True)
class ActionResult:
    newly_visible: set[str]
    newly_hidden: set[str]


class ActionEngine:
    """
    Translate action specs to Manim calls and advance a shared scene timeline clock.
    """

    def __init__(self, *, scene, state, ctx):
        self.scene = scene
        self.state = state
        self.ctx = ctx

    def _timeline_animation(self, duration: float):
        clock = getattr(self.state, "timeline_clock", None)
        if clock is None or duration <= 0:
            return None
        from manim import linear  # local import

        start = float(clock.get_value())
        end = start + float(duration)
        self.state.timeline_seconds = end
        return clock.animate(rate_func=linear).set_value(end)

    def _play_with_timeline(self, anims: list, *, duration: float) -> None:
        duration = float(max(0.0, duration))
        timeline_anim = self._timeline_animation(duration)

        if timeline_anim is not None:
            if anims:
                self.scene.play(*anims, timeline_anim, run_time=duration)
            else:
                self.scene.play(timeline_anim, run_time=duration)
            clock = getattr(self.state, "timeline_clock", None)
            if clock is not None:
                # Keep planned end time when running under mocked scenes in tests.
                self.state.timeline_seconds = max(self.state.timeline_seconds, float(clock.get_value()))
            return

        if anims:
            self.scene.play(*anims, run_time=duration)
        else:
            self.scene.wait(duration)
        self.state.timeline_seconds += duration

    def advance_timeline(self, duration: float) -> None:
        self._play_with_timeline([], duration=duration)

    def play_animations(self, anims: list, *, duration: float) -> None:
        self._play_with_timeline(list(anims), duration=duration)

    def run_action(self, action):
        if isinstance(action, WaitAction):
            self.advance_timeline(action.duration)
            return ActionResult(newly_visible=set(), newly_hidden=set())

        if not isinstance(action, PlayAction):
            raise TypeError(f"Unknown action type: {type(action)}")

        from manim import Create, FadeIn, FadeOut, Indicate, Transform, Write  # local import

        duration = float(action.duration or self.ctx.defaults.action_duration)

        if action.anim in {"fade_in", "fade_out", "write", "create", "indicate"}:
            anims = []
            for object_id in action.targets:
                mobj = self.state.objects[object_id]
                if action.anim == "fade_in":
                    anims.append(FadeIn(mobj))
                elif action.anim == "fade_out":
                    anims.append(FadeOut(mobj))
                elif action.anim == "write":
                    anims.append(Write(mobj))
                elif action.anim == "create":
                    anims.append(Create(mobj))
                elif action.anim == "indicate":
                    anims.append(Indicate(mobj))

            self._play_with_timeline(anims, duration=duration)

            if action.anim in {"fade_in", "write", "create"}:
                return ActionResult(newly_visible=set(action.targets), newly_hidden=set())
            if action.anim == "fade_out":
                return ActionResult(newly_visible=set(), newly_hidden=set(action.targets))
            return ActionResult(newly_visible=set(), newly_hidden=set())

        if action.anim == "transform":
            src = action.src or (action.targets[0] if len(action.targets) >= 1 else None)
            dst = action.dst or (action.targets[1] if len(action.targets) >= 2 else None)
            if not src or not dst:
                raise ValueError("transform requires src+dst (either fields or first 2 targets)")

            src_mobj = self.state.objects[src]
            dst_mobj = self.state.objects[dst]

            # Align target object with source before transform.
            dst_mobj.move_to(src_mobj.get_center())
            dst_mobj.match_height(src_mobj)

            self._play_with_timeline([Transform(src_mobj, dst_mobj)], duration=duration)

            # Rebind dst id to transformed source mobject for subsequent references.
            self.state.objects[dst] = src_mobj
            return ActionResult(newly_visible={src, dst}, newly_hidden=set())

        if action.anim in {"pin_to_corner", "title_pin"}:
            oid = run_pin_to_corner(engine=self, action=action)
            return ActionResult(newly_visible={str(oid)}, newly_hidden=set())

        raise ValueError(f"Unknown anim: {action.anim}")
