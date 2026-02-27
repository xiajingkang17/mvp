from __future__ import annotations

from layout.engine import Frame, SafeArea, compute_placements
from layout.params import default_params, sanitize_params
from schema.scene_plan_models import ObjectSpec


def _params_ok(
    template_type: str,
    slots: dict[str, str],
    params: dict,
    *,
    safe_area: SafeArea,
    frame: Frame,
    min_slot_w_norm: float,
    min_slot_h_norm: float,
) -> bool:
    placements = compute_placements(template_type, slots, safe_area=safe_area, frame=frame, params=params)
    min_w = frame.width * min_slot_w_norm
    min_h = frame.height * min_slot_h_norm
    for placement in placements.values():
        if placement.width < min_w or placement.height < min_h:
            return False
    return True


def refine_layout_params(
    template_type: str,
    slots: dict[str, str],
    *,
    llm_params: dict | None,
    object_specs: dict[str, ObjectSpec],
    objects: dict[str, object],
    base_sizes: dict[str, tuple[float, float]] | None,
    safe_area: SafeArea,
    frame: Frame,
    max_adjust: float,
    min_slot_w_norm: float,
    min_slot_h_norm: float,
    enabled: bool = True,
) -> dict:
    _ = object_specs, objects, base_sizes, max_adjust

    if not enabled:
        return sanitize_params(template_type, llm_params)

    llm_params_clean = sanitize_params(template_type, llm_params)
    default = default_params(template_type)

    candidates = [llm_params_clean, default]
    for params in candidates:
        if _params_ok(
            template_type,
            slots,
            params,
            safe_area=safe_area,
            frame=frame,
            min_slot_w_norm=min_slot_w_norm,
            min_slot_h_norm=min_slot_h_norm,
        ):
            return params

    return default
