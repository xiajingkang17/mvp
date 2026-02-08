from __future__ import annotations

from dataclasses import dataclass

from schema.scene_plan_models import PlayAction, WaitAction


@dataclass(frozen=True)
class ActionResult:
    newly_visible: set[str]
    newly_hidden: set[str]


class ActionEngine:
    """
    将动作规格（action spec）翻译成 Manim 调用。

    本模块对 Manim 使用延迟导入：即使未安装 Manim，非渲染工具也能正常使用。
    """

    def __init__(self, *, scene, state, ctx):
        self.scene = scene
        self.state = state
        self.ctx = ctx

    def run_action(self, action):
        if isinstance(action, WaitAction):
            self.scene.wait(action.duration)
            return ActionResult(newly_visible=set(), newly_hidden=set())

        if not isinstance(action, PlayAction):
            raise TypeError(f"Unknown action type: {type(action)}")

        from manim import Create, FadeIn, FadeOut, Indicate, Transform, Write  # 本地导入

        duration = action.duration or self.ctx.defaults.action_duration

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
            self.scene.play(*anims, run_time=duration)

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

            # 变换前先让目标对象与源对象的位置/尺度对齐。
            dst_mobj.move_to(src_mobj.get_center())
            dst_mobj.match_height(src_mobj)

            self.scene.play(Transform(src_mobj, dst_mobj), run_time=duration)

            # 将 dst id 绑定到变换后的源 mobject（后续引用 dst 时复用同一对象）。
            self.state.objects[dst] = src_mobj
            return ActionResult(newly_visible={src, dst}, newly_hidden=set())

        raise ValueError(f"Unknown anim: {action.anim}")
