from __future__ import annotations

import sys
import json
import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from manim import ORIGIN, Scene, ValueTracker, config

from layout.engine import Frame, Placement, SafeArea, compute_placements
from layout.refine_params import refine_layout_params
from layout.templates import build_template
from pipeline.config import load_app_config
from render.actions import ActionEngine
from render.registry import DEFAULT_REGISTRY
from render.runtime_state import RenderContext, RuntimeState
from schema.scene_plan_models import ScenePlan


def _anchor_to_aligned_edge(anchor: str):
    from manim import DOWN, LEFT, RIGHT, UP, DL, DR, UL, UR  # 本地导入

    anchor = (anchor or "C").upper()
    return {
        "C": None,
        "U": UP,
        "D": DOWN,
        "L": LEFT,
        "R": RIGHT,
        "UL": UL,
        "UR": UR,
        "DL": DL,
        "DR": DR,
    }.get(anchor, None)


def _anchor_point(center_x: float, center_y: float, width: float, height: float, *, anchor: str, pad: float):
    anchor = (anchor or "C").upper()
    pad_x = width * pad
    pad_y = height * pad

    left = center_x - width / 2 + pad_x
    right = center_x + width / 2 - pad_x
    bottom = center_y - height / 2 + pad_y
    top = center_y + height / 2 - pad_y

    if anchor == "UL":
        return (left, top)
    if anchor == "UR":
        return (right, top)
    if anchor == "DL":
        return (left, bottom)
    if anchor == "DR":
        return (right, bottom)
    if anchor == "U":
        return (center_x, top)
    if anchor == "D":
        return (center_x, bottom)
    if anchor == "L":
        return (left, center_y)
    if anchor == "R":
        return (right, center_y)
    return (center_x, center_y)


def apply_placement(mobj, placement, *, slot_padding: float):
    inner_w = max(0.01, placement.width * (1 - 2 * slot_padding))
    inner_h = max(0.01, placement.height * (1 - 2 * slot_padding))

    anchor_point = _anchor_point(
        placement.center_x,
        placement.center_y,
        placement.width,
        placement.height,
        anchor=placement.anchor,
        pad=slot_padding,
    )
    aligned_edge = _anchor_to_aligned_edge(placement.anchor)

    scale_factor = 1.0
    if getattr(mobj, "width", 0) > 0 and getattr(mobj, "height", 0) > 0:
        scale_factor = min(inner_w / mobj.width, inner_h / mobj.height)

    if hasattr(mobj, "composite_set_placement"):
        probe = mobj.copy()
        if scale_factor != 1.0:
            probe.scale(scale_factor, about_point=ORIGIN)
        if aligned_edge is None:
            ref = probe.get_center()
        else:
            ref = probe.get_critical_point(aligned_edge)
        tx = float(anchor_point[0]) - float(ref[0])
        ty = float(anchor_point[1]) - float(ref[1])
        mobj.composite_set_placement(scale_factor, tx, ty)
        return

    if scale_factor != 1.0:
        mobj.scale(scale_factor)

    if aligned_edge is None:
        mobj.move_to([anchor_point[0], anchor_point[1], 0])
    else:
        mobj.move_to([anchor_point[0], anchor_point[1], 0], aligned_edge=aligned_edge)


def _collect_scene_object_ids(scene) -> set[str]:
    ids: set[str] = set(scene.layout.slots.values())
    for action in scene.actions:
        if getattr(action, "targets", None):
            ids.update(action.targets)
        if getattr(action, "src", None):
            ids.add(action.src)
        if getattr(action, "dst", None):
            ids.add(action.dst)
    ids.update(scene.keep)
    return {x for x in ids if x}


def _ordered_unslotted_object_ids(scene, *, referenced: set[str]) -> list[str]:
    slotted_ids = set(scene.layout.slots.values())
    result: list[str] = []
    seen: set[str] = set()

    def _push(object_id: str | None) -> None:
        if not object_id:
            return
        if object_id not in referenced or object_id in slotted_ids:
            return
        if object_id in seen:
            return
        seen.add(object_id)
        result.append(object_id)

    for action in scene.actions:
        if getattr(action, "targets", None):
            for object_id in action.targets:
                _push(object_id)
        _push(getattr(action, "src", None))
        _push(getattr(action, "dst", None))

    for object_id in scene.keep:
        _push(object_id)

    for object_id in sorted(referenced):
        _push(object_id)

    return result


def _pick_container_slot_id(template, slots: dict[str, str]) -> str:
    if "right" in template.slots:
        return "right"
    free_slots = [slot_id for slot_id in template.slot_order if slot_id not in slots]
    if free_slots:
        return free_slots[0]
    return template.slot_order[0]


def _build_auto_stack_placements(
    scene,
    *,
    referenced: set[str],
    safe_area: SafeArea,
    frame: Frame,
    params: dict | None,
) -> dict[str, Placement]:
    unslotted = _ordered_unslotted_object_ids(scene, referenced=referenced)
    if not unslotted:
        return {}

    template = build_template(scene.layout.type, params or {})
    if not template.slot_order:
        return {}

    container_slot_id = _pick_container_slot_id(template, scene.layout.slots)
    container_object_id = scene.layout.slots.get(container_slot_id)
    if container_object_id and container_object_id in referenced and container_object_id not in unslotted:
        unslotted = [container_object_id, *unslotted]

    container = compute_placements(
        scene.layout.type,
        {container_slot_id: "__auto_container__"},
        safe_area=safe_area,
        frame=frame,
        params=params,
    )["__auto_container__"]

    total_h = container.height
    slot_w = container.width
    count = len(unslotted)
    cell_h = total_h / max(1, count)

    placements: dict[str, Placement] = {}
    for idx, object_id in enumerate(unslotted):
        cy = container.center_y + total_h / 2.0 - cell_h * (idx + 0.5)
        placements[object_id] = Placement(
            object_id=object_id,
            slot_id=f"auto:{container_slot_id}:{idx+1}",
            center_x=container.center_x,
            center_y=cy,
            width=slot_w,
            height=cell_h,
            anchor="C",
        )
    return placements


class PlanScene(Scene):
    def construct(self):
        plan_path = Path(os.environ.get("SCENE_PLAN", "cases/demo_001/scene_plan.json"))
        plan = ScenePlan.model_validate(json.loads(plan_path.read_text(encoding="utf-8")))

        app = load_app_config()
        ctx = RenderContext(app=app, frame_width=float(config.frame_width), frame_height=float(config.frame_height))

        state = RuntimeState()
        state.timeline_clock = ValueTracker(0.0)
        state.timeline_seconds = 0.0
        registry = DEFAULT_REGISTRY

        from components.base import ComponentDefaults

        build_defaults = ComponentDefaults(
            font=ctx.defaults.font,
            text_font_size=ctx.defaults.text_font_size,
            bullet_font_size=ctx.defaults.bullet_font_size,
            formula_font_size=ctx.defaults.formula_font_size,
        )

        action_engine = ActionEngine(scene=self, state=state, ctx=ctx)

        safe = SafeArea(
            left=ctx.app.safe_area.left,
            right=ctx.app.safe_area.right,
            top=ctx.app.safe_area.top,
            bottom=ctx.app.safe_area.bottom,
        )
        frame = Frame(width=ctx.frame_width, height=ctx.frame_height)

        for scene in plan.scenes:
            referenced = _collect_scene_object_ids(scene)

            # Clear objects that are visible but not needed by this scene, before laying out new content.
            stale_ids = sorted([oid for oid in state.visible if oid not in referenced])
            if stale_ids:
                from manim import FadeOut

                stale_mobjects = []
                seen = set()
                for oid in stale_ids:
                    mobj = state.objects.get(oid)
                    if mobj is None:
                        continue
                    mid = id(mobj)
                    if mid in seen:
                        continue
                    seen.add(mid)
                    stale_mobjects.append(mobj)

                if stale_mobjects:
                    action_engine.play_animations([FadeOut(m) for m in stale_mobjects], duration=ctx.defaults.action_duration)
                for oid in stale_ids:
                    state.visible.discard(oid)

            for object_id in referenced:
                if not object_id:
                    continue
                if object_id in state.objects:
                    continue
                spec = plan.objects[object_id]
                mobj = registry.build(spec, defaults=build_defaults)
                state.base_sizes[object_id] = (float(getattr(mobj, "width", 0.0)), float(getattr(mobj, "height", 0.0)))
                if spec.z_index is not None:
                    mobj.z_index = spec.z_index
                state.objects[object_id] = mobj
                if hasattr(mobj, "composite_set_time"):
                    mobj.composite_set_time(state.timeline_seconds)

                    def _time_updater(m, dt, _state=state):
                        clock = getattr(_state, "timeline_clock", None)
                        if clock is None:
                            return
                        setter = getattr(m, "composite_set_time", None)
                        if callable(setter):
                            setter(float(clock.get_value()))

                    mobj.add_updater(_time_updater)
                    mobj.composite_time_updater = _time_updater

            refined_params = refine_layout_params(
                scene.layout.type,
                scene.layout.slots,
                llm_params=scene.layout.params,
                object_specs=plan.objects,
                objects=state.objects,
                base_sizes=state.base_sizes,
                safe_area=safe,
                frame=frame,
                max_adjust=ctx.app.layout_refine.max_adjust,
                min_slot_w_norm=ctx.app.layout_refine.min_slot_w_norm,
                min_slot_h_norm=ctx.app.layout_refine.min_slot_h_norm,
                enabled=ctx.app.layout_refine.enabled,
            )

            placements = compute_placements(
                scene.layout.type,
                scene.layout.slots,
                safe_area=safe,
                frame=frame,
                params=refined_params,
            )

            auto_placements = _build_auto_stack_placements(
                scene,
                referenced=referenced,
                safe_area=safe,
                frame=frame,
                params=refined_params,
            )
            placements.update(auto_placements)

            for object_id, placement in placements.items():
                apply_placement(state.objects[object_id], placement, slot_padding=ctx.app.slot_padding)

            for action in scene.actions:
                result = action_engine.run_action(action)
                for oid in result.newly_visible:
                    state.visible.add(oid)
                for oid in result.newly_hidden:
                    state.visible.discard(oid)

            # 自动清理本 scene 未声明保留的对象。
            keep_set = set(scene.keep)
            to_clear_ids = sorted([oid for oid in state.visible if oid not in keep_set])
            if to_clear_ids:
                from manim import FadeOut

                unique_mobjects = []
                seen = set()
                for oid in to_clear_ids:
                    mobj = state.objects.get(oid)
                    if mobj is None:
                        continue
                    mid = id(mobj)
                    if mid in seen:
                        continue
                    seen.add(mid)
                    unique_mobjects.append(mobj)

                action_engine.play_animations([FadeOut(m) for m in unique_mobjects], duration=ctx.defaults.action_duration)
                for oid in to_clear_ids:
                    state.visible.discard(oid)
