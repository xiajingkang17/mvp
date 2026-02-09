from __future__ import annotations

import sys
import json
import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from manim import Scene, config

from layout.engine import Frame, SafeArea, compute_placements
from layout.refine_params import refine_layout_params
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

    if getattr(mobj, "width", 0) > 0 and getattr(mobj, "height", 0) > 0:
        scale_factor = min(inner_w / mobj.width, inner_h / mobj.height)
        mobj.scale(scale_factor)

    anchor_point = _anchor_point(
        placement.center_x,
        placement.center_y,
        placement.width,
        placement.height,
        anchor=placement.anchor,
        pad=slot_padding,
    )
    aligned_edge = _anchor_to_aligned_edge(placement.anchor)
    if aligned_edge is None:
        mobj.move_to([anchor_point[0], anchor_point[1], 0])
    else:
        mobj.move_to([anchor_point[0], anchor_point[1], 0], aligned_edge=aligned_edge)


class PlanScene(Scene):
    def construct(self):
        plan_path = Path(os.environ.get("SCENE_PLAN", "cases/demo_001/scene_plan.json"))
        plan = ScenePlan.model_validate(json.loads(plan_path.read_text(encoding="utf-8")))

        app = load_app_config()
        ctx = RenderContext(app=app, frame_width=float(config.frame_width), frame_height=float(config.frame_height))

        state = RuntimeState()
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
            referenced = set(scene.layout.slots.values())
            for action in scene.actions:
                if getattr(action, "targets", None):
                    referenced.update(action.targets)
                if getattr(action, "src", None):
                    referenced.add(action.src)
                if getattr(action, "dst", None):
                    referenced.add(action.dst)
            referenced.update(scene.keep)

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

                self.play(*[FadeOut(m) for m in unique_mobjects], run_time=ctx.defaults.action_duration)
                for oid in to_clear_ids:
                    state.visible.discard(oid)
