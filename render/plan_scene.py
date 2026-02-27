from __future__ import annotations

import sys
import json
import os
import re
from dataclasses import replace
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


_NARRATIVE_EQ_RE = re.compile(
    r"([A-Za-z\\μΜΑ-Ωα-ω][A-Za-z0-9\\μΜΑ-Ωα-ω_\\^{}]*(?:\s*[=+\-*/]\s*[A-Za-z0-9\\μΜΑ-Ωα-ω_\\^{}]+)+)"
)


_NARRATIVE_RESERVED_ID = "__reserved_narrative__"
_NARRATIVE_RESERVED_MARGIN = 0.18
_NARRATIVE_SAFE_GAP = 0.08
_MIN_TOP_WORKSPACE_NORM = 0.24


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


def apply_placement(mobj, placement, *, slot_padding: float, base_size: tuple[float, float] | None = None):
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

    base_w = base_h = 0.0
    if base_size is not None:
        base_w, base_h = float(base_size[0]), float(base_size[1])

    scale_factor = 1.0
    if base_w > 0 and base_h > 0:
        # Use the original (unscaled) size as the reference to avoid compounding
        # scale across scenes when placements are re-applied.
        scale_factor = min(inner_w / base_w, inner_h / base_h)
    elif getattr(mobj, "width", 0) > 0 and getattr(mobj, "height", 0) > 0:
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
        setter = getattr(mobj, "composite_set_placement_absolute", None)
        if callable(setter):
            setter(scale_factor, tx, ty)
        else:
            # Back-compat: old composite placement API is relative/multiplicative.
            mobj.composite_set_placement(scale_factor, tx, ty)
        return

    if scale_factor != 1.0:
        # Apply absolute scaling relative to the object's base size when available,
        # so re-running layout doesn't gradually drift.
        if base_w > 0 and getattr(mobj, "width", 0) > 0:
            target_w = scale_factor * base_w
            mul = float(target_w) / float(mobj.width) if float(mobj.width) != 0 else 1.0
            if mul != 1.0:
                mobj.scale(mul, about_point=ORIGIN)
        else:
            mobj.scale(scale_factor, about_point=ORIGIN)

    if aligned_edge is None:
        mobj.move_to([anchor_point[0], anchor_point[1], 0])
    else:
        mobj.move_to([anchor_point[0], anchor_point[1], 0], aligned_edge=aligned_edge)


def _collect_scene_object_ids(scene) -> set[str]:
    ids: set[str] = set(scene.layout.slots.values())
    placements = getattr(scene.layout, "placements", {})
    if isinstance(placements, dict):
        ids.update(placements.keys())
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
    placement_ids = set(getattr(scene.layout, "placements", {}).keys())
    slotted_ids = set(scene.layout.slots.values()) | placement_ids
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


def _build_free_placements(layout, *, safe_area: SafeArea, frame: Frame) -> dict[str, Placement]:
    safe_w = max(1e-6, 1.0 - safe_area.left - safe_area.right)
    safe_h = max(1e-6, 1.0 - safe_area.top - safe_area.bottom)

    placements: dict[str, Placement] = {}
    for object_id, spec in layout.placements.items():
        cx_norm = safe_area.left + float(spec.cx) * safe_w
        cy_norm = safe_area.bottom + float(spec.cy) * safe_h
        w_norm = float(spec.w) * safe_w
        h_norm = float(spec.h) * safe_h

        center_x = (cx_norm - 0.5) * frame.width
        center_y = (cy_norm - 0.5) * frame.height

        placements[object_id] = Placement(
            object_id=object_id,
            slot_id=f"free:{object_id}",
            center_x=center_x,
            center_y=center_y,
            width=w_norm * frame.width,
            height=h_norm * frame.height,
            anchor=str(spec.anchor or "C").upper(),
        )
    return placements


def _safe_bounds(*, safe_area: SafeArea, frame: Frame) -> tuple[float, float, float, float]:
    x_min = -frame.width / 2.0 + safe_area.left * frame.width
    x_max = frame.width / 2.0 - safe_area.right * frame.width
    y_min = -frame.height / 2.0 + safe_area.bottom * frame.height
    y_max = frame.height / 2.0 - safe_area.top * frame.height
    return x_min, x_max, y_min, y_max


def _narrative_reserved_placement(
    overlay,
    *,
    frame: Frame,
    safe_area: SafeArea,
) -> Placement | None:
    if overlay is None:
        return None
    center = overlay.get_center()
    max_width = frame.width * max(0.2, 1.0 - safe_area.left - safe_area.right)
    width = min(max_width, float(getattr(overlay, "width", 0.0)) + _NARRATIVE_RESERVED_MARGIN)
    height = float(getattr(overlay, "height", 0.0)) + _NARRATIVE_RESERVED_MARGIN
    if width <= 0.0 or height <= 0.0:
        return None
    return Placement(
        object_id=_NARRATIVE_RESERVED_ID,
        slot_id="reserved:narrative",
        center_x=float(center[0]),
        center_y=float(center[1]),
        width=width,
        height=height,
        anchor="C",
    )


def _safe_area_with_narrative_reserve(
    base_safe: SafeArea,
    *,
    frame: Frame,
    reserve: Placement | None,
    gap: float = _NARRATIVE_SAFE_GAP,
) -> SafeArea:
    if reserve is None:
        return base_safe
    y_min = -frame.height / 2.0
    reserved_top = reserve.center_y + reserve.height / 2.0 + max(0.0, gap)
    required_bottom = (reserved_top - y_min) / frame.height
    max_bottom = max(base_safe.bottom, 1.0 - base_safe.top - _MIN_TOP_WORKSPACE_NORM)
    next_bottom = min(max_bottom, max(base_safe.bottom, required_bottom))
    if next_bottom <= base_safe.bottom + 1e-6:
        return base_safe
    return SafeArea(
        left=base_safe.left,
        right=base_safe.right,
        top=base_safe.top,
        bottom=next_bottom,
    )


def _clamp_center(*, cx: float, cy: float, w: float, h: float, bounds: tuple[float, float, float, float]) -> tuple[float, float]:
    x_min, x_max, y_min, y_max = bounds
    half_w = max(0.01, w / 2.0)
    half_h = max(0.01, h / 2.0)
    clamped_x = min(max(cx, x_min + half_w), x_max - half_w)
    clamped_y = min(max(cy, y_min + half_h), y_max - half_h)
    return clamped_x, clamped_y


def _overlap_amount(a: Placement, b: Placement) -> tuple[float, float]:
    left = max(a.center_x - a.width / 2.0, b.center_x - b.width / 2.0)
    right = min(a.center_x + a.width / 2.0, b.center_x + b.width / 2.0)
    bottom = max(a.center_y - a.height / 2.0, b.center_y - b.height / 2.0)
    top = min(a.center_y + a.height / 2.0, b.center_y + b.height / 2.0)
    return right - left, top - bottom


def _resolve_free_placement_overlaps(
    placements: dict[str, Placement],
    *,
    object_priorities: dict[str, int],
    safe_area: SafeArea,
    frame: Frame,
    min_gap: float,
    max_rounds: int = 20,
) -> dict[str, Placement]:
    if len(placements) < 2:
        return placements

    bounds = _safe_bounds(safe_area=safe_area, frame=frame)
    adjusted = dict(placements)
    ordered_ids = sorted(adjusted.keys())

    for _ in range(max_rounds):
        changed = False
        for i in range(len(ordered_ids)):
            for j in range(i + 1, len(ordered_ids)):
                a_id = ordered_ids[i]
                b_id = ordered_ids[j]
                a = adjusted[a_id]
                b = adjusted[b_id]
                ox, oy = _overlap_amount(a, b)
                if ox <= 0.0 or oy <= 0.0:
                    continue
                if ox <= min_gap or oy <= min_gap:
                    continue

                pa = int(object_priorities.get(a_id, 9))
                pb = int(object_priorities.get(b_id, 9))
                if pa <= pb:
                    fixed_id, move_id = a_id, b_id
                else:
                    fixed_id, move_id = b_id, a_id

                fixed = adjusted[fixed_id]
                mover = adjusted[move_id]
                move_x = ox + min_gap
                move_y = oy + min_gap

                if move_x < move_y:
                    sign = 1.0 if mover.center_x >= fixed.center_x else -1.0
                    next_cx = mover.center_x + sign * move_x
                    next_cy = mover.center_y
                else:
                    sign = 1.0 if mover.center_y >= fixed.center_y else -1.0
                    next_cx = mover.center_x
                    next_cy = mover.center_y + sign * move_y

                next_cx, next_cy = _clamp_center(
                    cx=next_cx,
                    cy=next_cy,
                    w=mover.width,
                    h=mover.height,
                    bounds=bounds,
                )
                if abs(next_cx - mover.center_x) < 1e-6 and abs(next_cy - mover.center_y) < 1e-6:
                    continue

                adjusted[move_id] = replace(mover, center_x=next_cx, center_y=next_cy)
                changed = True

        if not changed:
            break

    return adjusted


def _translate_only(mobj, *, dx: float, dy: float) -> None:
    if abs(dx) < 1e-6 and abs(dy) < 1e-6:
        return
    if hasattr(mobj, "composite_set_placement"):
        setter = getattr(mobj, "composite_set_placement", None)
        if callable(setter):
            setter(1.0, float(dx), float(dy))
            return
    mobj.shift([float(dx), float(dy), 0.0])


def _split_equation_like_chunks(text: str) -> list[tuple[str, str]]:
    if not text:
        return []
    chunks: list[tuple[str, str]] = []
    cursor = 0
    for match in _NARRATIVE_EQ_RE.finditer(text):
        start, end = match.span()
        if start > cursor:
            chunks.append(("text", text[cursor:start]))
        chunks.append(("math", match.group(1)))
        cursor = end
    if cursor < len(text):
        chunks.append(("text", text[cursor:]))
    return chunks


def _normalize_narrative_math(expr: str) -> str:
    from components.common.latex_subscripts import shorten_latex_subscripts

    fixed = expr.replace("μ", r"\mu ").replace("×", r"\times ")
    fixed = shorten_latex_subscripts(fixed, max_letters=2)
    return fixed.strip()


def _render_narrative_line(line: str, *, font: str, font_size: int):
    from manim import DOWN, LEFT, RIGHT, MathTex, Text, VGroup

    from components.common.inline_math import split_inline_math_segments

    kwargs = {"font": font, "font_size": font_size}
    parts = []
    for kind, value in split_inline_math_segments(line):
        if kind == "math":
            expr = _normalize_narrative_math(value)
            if not expr:
                continue
            try:
                parts.append(MathTex(expr, font_size=font_size))
            except Exception:  # noqa: BLE001
                parts.append(Text(f"${value}$", **kwargs))
            continue

        for sub_kind, sub_value in _split_equation_like_chunks(value):
            if not sub_value:
                continue
            if sub_kind == "text":
                parts.append(Text(sub_value, **kwargs))
            else:
                expr = _normalize_narrative_math(sub_value)
                if not expr:
                    continue
                try:
                    parts.append(MathTex(expr, font_size=font_size))
                except Exception:  # noqa: BLE001
                    parts.append(Text(sub_value, **kwargs))

    if not parts:
        parts = [Text(" ", **kwargs)]
        parts[0].set_opacity(0.0)

    line_group = VGroup(*parts)
    line_group.arrange(RIGHT, aligned_edge=DOWN, buff=max(0.04, font_size * 0.0014))
    return line_group


def _build_narrative_overlay(text: str, *, font: str, frame: Frame, safe_area: SafeArea):
    from manim import BLACK, BackgroundRectangle, Text, VGroup, DOWN, LEFT

    content = text.strip()
    if not content:
        return None

    lines = content.splitlines() or [content]
    rendered_lines = [_render_narrative_line(line, font=font, font_size=24) for line in lines]
    if len(rendered_lines) == 1:
        label = rendered_lines[0]
    else:
        label = VGroup(*rendered_lines)
        label.arrange(DOWN, aligned_edge=LEFT, buff=0.16)

    # Ensure plain text fallback keeps expected spacing behavior.
    if isinstance(label, Text):
        label.line_spacing = 0.85

    max_width = frame.width * max(0.2, 1.0 - safe_area.left - safe_area.right) * 0.96
    if label.width > max_width:
        label.scale_to_fit_width(max_width)

    bg = BackgroundRectangle(label, color=BLACK, fill_opacity=0.6, buff=0.12, stroke_opacity=0.0)
    overlay = VGroup(bg, label)
    y = (-frame.height / 2.0) + safe_area.bottom * frame.height + overlay.height / 2.0 + 0.06
    overlay.move_to([0.0, y, 0.0])
    overlay.z_index = 1000
    return overlay


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
        narrative_overlay = None

        for scene in plan.scenes:
            referenced = _collect_scene_object_ids(scene)

            if narrative_overlay is not None:
                from manim import FadeOut

                self.play(FadeOut(narrative_overlay), run_time=0.2)
                self.remove(narrative_overlay)
                narrative_overlay = None

            scene_narrative = (scene.narrative or "").strip()
            narrative_reserved = None
            scene_safe = safe
            if scene_narrative:
                from manim import FadeIn

                narrative_overlay = _build_narrative_overlay(
                    scene_narrative,
                    font=ctx.defaults.font,
                    frame=frame,
                    safe_area=safe,
                )
                narrative_reserved = _narrative_reserved_placement(
                    narrative_overlay,
                    frame=frame,
                    safe_area=safe,
                )
                scene_safe = _safe_area_with_narrative_reserve(
                    safe,
                    frame=frame,
                    reserve=narrative_reserved,
                )
                if narrative_overlay is not None:
                    self.play(FadeIn(narrative_overlay), run_time=0.25)

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
                    setter = getattr(mobj, "composite_set_time", None)
                    clock = getattr(state, "timeline_clock", None)
                    if clock is None:
                        origin_t = float(state.timeline_seconds)
                    else:
                        origin_t = float(clock.get_value())
                    mobj.composite_time_origin = origin_t
                    if callable(setter):
                        setter(0.0)

                    def _reset_time_origin(new_origin_t: float, _setter=setter, _mobj=mobj):
                        _mobj.composite_time_origin = float(new_origin_t)
                        if callable(_setter):
                            _setter(0.0)

                    mobj.composite_reset_time_origin = _reset_time_origin

                    def _time_updater(m, dt, _state=state):
                        clock = getattr(_state, "timeline_clock", None)
                        if clock is None:
                            return
                        setter = getattr(m, "composite_set_time", None)
                        if callable(setter):
                            origin = float(getattr(m, "composite_time_origin", 0.0))
                            local_t = float(clock.get_value()) - origin
                            setter(local_t if local_t >= 0.0 else 0.0)

                    mobj.add_updater(_time_updater)
                    mobj.composite_time_updater = _time_updater

            if scene.layout.type == "free":
                placements = _build_free_placements(scene.layout, safe_area=scene_safe, frame=frame)
            else:
                refined_params = refine_layout_params(
                    scene.layout.type,
                    scene.layout.slots,
                    llm_params=scene.layout.params,
                    object_specs=plan.objects,
                    objects=state.objects,
                    base_sizes=state.base_sizes,
                    safe_area=scene_safe,
                    frame=frame,
                    max_adjust=ctx.app.layout_refine.max_adjust,
                    min_slot_w_norm=ctx.app.layout_refine.min_slot_w_norm,
                    min_slot_h_norm=ctx.app.layout_refine.min_slot_h_norm,
                    enabled=ctx.app.layout_refine.enabled,
                )

                placements = compute_placements(
                    scene.layout.type,
                    scene.layout.slots,
                    safe_area=scene_safe,
                    frame=frame,
                    params=refined_params,
                )

                auto_placements = _build_auto_stack_placements(
                    scene,
                    referenced=referenced,
                    safe_area=scene_safe,
                    frame=frame,
                    params=refined_params,
                )
                placements.update(auto_placements)

            carry_reference: dict[str, Placement] = {}
            for oid in referenced:
                if oid in placements or oid not in state.visible:
                    continue
                mobj = state.objects.get(oid)
                if mobj is None:
                    continue
                center = mobj.get_center()
                carry_reference[oid] = Placement(
                    object_id=oid,
                    slot_id=f"carry:{oid}",
                    center_x=float(center[0]),
                    center_y=float(center[1]),
                    width=float(getattr(mobj, "width", 0.1) or 0.1),
                    height=float(getattr(mobj, "height", 0.1) or 0.1),
                    anchor="C",
                )

            overlap_space = dict(placements)
            overlap_space.update(carry_reference)
            if narrative_reserved is not None:
                overlap_space[narrative_reserved.object_id] = narrative_reserved
            object_priorities = {oid: int(plan.objects[oid].priority) for oid in overlap_space if oid in plan.objects}
            for oid in carry_reference:
                object_priorities[oid] = 0
            if narrative_reserved is not None:
                object_priorities[narrative_reserved.object_id] = -1000

            resolved = _resolve_free_placement_overlaps(
                overlap_space,
                object_priorities=object_priorities,
                safe_area=scene_safe,
                frame=frame,
                min_gap=max(0.06, min(frame.width, frame.height) * 0.01),
            )
            placements = {oid: resolved.get(oid, placement) for oid, placement in placements.items()}

            for oid, prior in carry_reference.items():
                target = resolved.get(oid)
                if target is None:
                    continue
                dx = float(target.center_x - prior.center_x)
                dy = float(target.center_y - prior.center_y)
                mobj = state.objects.get(oid)
                if mobj is None:
                    continue
                _translate_only(mobj, dx=dx, dy=dy)

            for object_id, placement in placements.items():
                apply_placement(
                    state.objects[object_id],
                    placement,
                    slot_padding=ctx.app.slot_padding,
                    base_size=state.base_sizes.get(object_id),
                )

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
