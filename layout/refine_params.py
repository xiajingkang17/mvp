from __future__ import annotations

from dataclasses import dataclass

from layout.engine import Frame, SafeArea, compute_placements
from layout.params import clamp, default_params, normalize_weights, sanitize_params
from schema.scene_plan_models import ObjectSpec


@dataclass(frozen=True)
class ObjectMetrics:
    width: float
    height: float
    area: float
    aspect: float
    importance: float
    demand: float


SIZE_LEVEL_FACTOR = {
    "S": 0.85,
    "M": 1.0,
    "L": 1.2,
    "XL": 1.4,
}


def _priority_factor(priority: int) -> float:
    # priority: 1..9 -> 1.15 .. 0.75
    return max(0.6, 1.15 - 0.05 * max(priority - 1, 0))


def _size_level_factor(level: str | None) -> float:
    if not level:
        return SIZE_LEVEL_FACTOR["M"]
    return SIZE_LEVEL_FACTOR.get(level.upper(), SIZE_LEVEL_FACTOR["M"])


def _compute_metrics(spec: ObjectSpec, width: float, height: float) -> ObjectMetrics:
    width = max(float(width), 0.01)
    height = max(float(height), 0.01)
    area = width * height
    aspect = width / height if height > 0 else 1.0
    importance = _size_level_factor(spec.style.get("size_level")) * _priority_factor(spec.priority)
    demand = area * importance
    return ObjectMetrics(
        width=width,
        height=height,
        area=area,
        aspect=aspect,
        importance=importance,
        demand=demand,
    )


def _proposal_left_ratio(slots: dict[str, str], metrics: dict[str, ObjectMetrics]) -> float:
    left_id = slots.get("left")
    right_id = slots.get("right")
    d_left = metrics.get(left_id).demand if left_id in metrics else 1.0
    d_right = metrics.get(right_id).demand if right_id in metrics else 1.0
    if d_left + d_right <= 0:
        return 0.5
    return clamp(d_left / (d_left + d_right), 0.3, 0.7)


def _proposal_row_weights(slots: dict[str, str], metrics: dict[str, ObjectMetrics], rows: int) -> list[float]:
    weights = []
    for i in range(rows):
        left_id = slots.get(f"left{i+1}")
        right_id = slots.get(f"right{i+1}")
        d_left = metrics.get(left_id).demand if left_id in metrics else 0.0
        d_right = metrics.get(right_id).demand if right_id in metrics else 0.0
        weights.append(max(d_left + d_right, 1e-6))
    return normalize_weights(weights)


def _blend_scalar(llm_value: float, proposed: float, max_adjust: float, min_value: float, max_value: float) -> float:
    low = llm_value - max_adjust
    high = llm_value + max_adjust
    return clamp(clamp(proposed, low, high), min_value, max_value)


def _blend_weights(llm_weights: list[float], proposed: list[float], max_adjust: float) -> list[float]:
    if len(llm_weights) != len(proposed):
        return proposed
    blended = []
    for w0, w1 in zip(llm_weights, proposed, strict=False):
        blended.append(clamp(w1, w0 - max_adjust, w0 + max_adjust))
    return normalize_weights(blended)


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
    if not enabled:
        return sanitize_params(template_type, llm_params)

    metrics: dict[str, ObjectMetrics] = {}
    for object_id in set(slots.values()):
        if not object_id:
            continue
        spec = object_specs.get(object_id)
        mobj = objects.get(object_id)
        if spec is None or mobj is None:
            continue
        if base_sizes and object_id in base_sizes:
            width, height = base_sizes[object_id]
        else:
            width = float(getattr(mobj, "width", 0.0))
            height = float(getattr(mobj, "height", 0.0))
        metrics[object_id] = _compute_metrics(spec, width, height)

    llm_params_clean = sanitize_params(template_type, llm_params)
    default = default_params(template_type)

    proposed = llm_params_clean
    if template_type == "left_right":
        proposed = {"left_ratio": _proposal_left_ratio(slots, metrics)}
    elif template_type == "left3_right3":
        proposed = {"row_weights": _proposal_row_weights(slots, metrics, 3)}
    elif template_type == "left4_right4":
        proposed = {"row_weights": _proposal_row_weights(slots, metrics, 4)}

    refined = proposed
    if template_type == "left_right":
        llm_ratio = float(llm_params_clean.get("left_ratio", 0.5))
        refined = {
            "left_ratio": _blend_scalar(llm_ratio, float(proposed.get("left_ratio", 0.5)), max_adjust, 0.3, 0.7)
        }
    elif template_type in {"left3_right3", "left4_right4"}:
        llm_weights = list(llm_params_clean.get("row_weights", proposed.get("row_weights", [])))
        refined = {"row_weights": _blend_weights(llm_weights, proposed.get("row_weights", []), max_adjust)}

    candidates = [refined, llm_params_clean, default]
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
