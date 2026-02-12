from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PinToCornerParams:
    start: str = "CENTER"  # "CENTER" | "KEEP"
    corner: str = "UL"
    buff: float = 0.35

    # Relative to the base size captured at object creation time.
    start_scale: float = 1.0
    scale_to: float = 0.62

    appear: bool = True
    appear_shift: str = "UP"
    appear_scale: float = 1.06

    focus: bool = True
    focus_scale: float = 1.03


def _dir_vec(name: str):
    from manim import DOWN, LEFT, RIGHT, UP  # local import

    name = (name or "").upper()
    return {
        "UP": UP,
        "DOWN": DOWN,
        "LEFT": LEFT,
        "RIGHT": RIGHT,
    }.get(name, UP)


def _corner_vec(name: str):
    from manim import DL, DOWN, DR, LEFT, RIGHT, UL, UP, UR  # local import

    name = (name or "UL").upper()
    return {
        "UL": UL,
        "UR": UR,
        "DL": DL,
        "DR": DR,
        "U": UP,
        "D": DOWN,
        "L": LEFT,
        "R": RIGHT,
    }.get(name, UL)


def _parse_params(kwargs: dict[str, Any] | None) -> PinToCornerParams:
    kwargs = kwargs or {}
    base = PinToCornerParams()
    return PinToCornerParams(
        start=str(kwargs.get("start", base.start)),
        corner=str(kwargs.get("corner", base.corner)),
        buff=float(kwargs.get("buff", base.buff)),
        scale_to=float(kwargs.get("scale_to", base.scale_to)),
        start_scale=float(kwargs.get("start_scale", base.start_scale)),
        appear=bool(kwargs.get("appear", base.appear)),
        appear_shift=str(kwargs.get("appear_shift", base.appear_shift)),
        appear_scale=float(kwargs.get("appear_scale", base.appear_scale)),
        focus=bool(kwargs.get("focus", base.focus)),
        focus_scale=float(kwargs.get("focus_scale", base.focus_scale)),
    )


def run_pin_to_corner(*, engine, action) -> str:
    """
    A generic "center pop -> pin to corner" motion that works for any object.

    Expected action:
      - anim: "pin_to_corner" (or legacy alias: "title_pin")
      - targets: [object_id]
      - duration: total duration (optional)
      - kwargs:
          start: "CENTER"|"KEEP"
          corner: "UL"|"UR"|"DL"|"DR"|"U"|"D"|"L"|"R"
          scale_to: float (relative to base size captured at creation)
          start_scale: float (relative to base size captured at creation)
          buff: float
          appear: bool
          appear_shift: "UP"|"DOWN"|"LEFT"|"RIGHT"
          appear_scale: float
          focus: bool
          focus_scale: float
    """
    from manim import ORIGIN, FadeIn, there_and_back, smooth  # local import

    if not action.targets:
        raise ValueError("pin_to_corner requires targets[0]")

    object_id = str(action.targets[0])
    mobj = engine.state.objects[object_id]
    base_w, base_h = engine.state.base_sizes.get(object_id, (0.0, 0.0))

    params = _parse_params(getattr(action, "kwargs", None))

    total = float(action.duration or engine.ctx.defaults.action_duration)
    total = float(max(0.01, total))

    # Default timing split tuned for "breathing" without feeling slow.
    appear_t = total * 0.35
    focus_t = total * 0.15
    move_t = max(0.01, total - appear_t - focus_t)

    corner = _corner_vec(params.corner)

    if str(params.start).upper() == "CENTER":
        mobj.move_to(ORIGIN)
        if base_w > 0 and base_h > 0:
            target_w = base_w * float(params.start_scale)
            target_h = base_h * float(params.start_scale)
            cur_w = float(getattr(mobj, "width", 0.0) or 0.0)
            cur_h = float(getattr(mobj, "height", 0.0) or 0.0)
            if cur_w > 0 and cur_h > 0:
                mobj.scale(min(target_w / cur_w, target_h / cur_h))

    # 1) Appear (only if not already visible).
    if params.appear and object_id not in engine.state.visible:
        shift = 0.25 * _dir_vec(params.appear_shift)
        engine.play_animations(
            [FadeIn(mobj, shift=shift, scale=float(params.appear_scale))],
            duration=appear_t,
        )
        engine.state.visible.add(object_id)

    # 2) Focus pulse (works for both newly visible and already visible).
    if params.focus:
        engine.play_animations(
            [mobj.animate(rate_func=there_and_back).scale(float(params.focus_scale))],
            duration=focus_t,
        )

    # 3) Pin to corner and scale to target.
    scale_factor = 1.0
    if base_w > 0 and base_h > 0:
        target_w = base_w * float(params.scale_to)
        target_h = base_h * float(params.scale_to)
        cur_w = float(getattr(mobj, "width", 0.0) or 0.0)
        cur_h = float(getattr(mobj, "height", 0.0) or 0.0)
        if cur_w > 0 and cur_h > 0:
            scale_factor = min(target_w / cur_w, target_h / cur_h)

    engine.play_animations(
        [mobj.animate(rate_func=smooth).to_corner(corner, buff=float(params.buff)).scale(scale_factor)],
        duration=move_t,
    )

    return object_id

