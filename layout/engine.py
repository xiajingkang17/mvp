from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .templates import SlotBBox, build_template


@dataclass(frozen=True)
class SafeArea:
    left: float
    right: float
    top: float
    bottom: float


@dataclass(frozen=True)
class Frame:
    width: float
    height: float


@dataclass(frozen=True)
class Placement:
    object_id: str
    slot_id: str
    center_x: float
    center_y: float
    width: float
    height: float
    anchor: str


def _apply_safe_area(bbox: SlotBBox, safe: SafeArea) -> SlotBBox:
    safe_w = 1.0 - safe.left - safe.right
    safe_h = 1.0 - safe.top - safe.bottom
    return SlotBBox(
        cx=safe.left + bbox.cx * safe_w,
        cy=safe.bottom + bbox.cy * safe_h,
        w=bbox.w * safe_w,
        h=bbox.h * safe_h,
        anchor=bbox.anchor,
    )


def _norm_to_frame_center(cx: float, cy: float, frame: Frame) -> tuple[float, float]:
    x = (cx - 0.5) * frame.width
    y = (cy - 0.5) * frame.height
    return x, y


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _apply_slot_size_override(slot_id: str, bbox: SlotBBox, params: dict[str, Any] | None) -> SlotBBox:
    if not isinstance(params, dict):
        return bbox
    raw_scales = params.get("slot_scales")
    if not isinstance(raw_scales, dict):
        return bbox
    item = raw_scales.get(slot_id)
    if not isinstance(item, dict):
        return bbox

    w_raw = item.get("w", item.get("width", 1.0))
    h_raw = item.get("h", item.get("height", 1.0))
    try:
        w_scale = float(w_raw)
        h_scale = float(h_raw)
    except (TypeError, ValueError):
        return bbox

    # Keep slot overrides conservative to avoid uncontrolled overlap.
    w_scale = _clamp(w_scale, 0.2, 1.0)
    h_scale = _clamp(h_scale, 0.2, 1.0)
    return SlotBBox(cx=bbox.cx, cy=bbox.cy, w=bbox.w * w_scale, h=bbox.h * h_scale, anchor=bbox.anchor)


def compute_placements(
    template_type: str,
    slots: dict[str, str],
    *,
    safe_area: SafeArea,
    frame: Frame,
    params: dict | None = None,
) -> dict[str, Placement]:
    try:
        template = build_template(template_type, params)
    except KeyError as exc:
        raise ValueError(f"Unknown template: {template_type}") from exc

    placements: dict[str, Placement] = {}
    for slot_id, object_id in slots.items():
        if slot_id not in template.slots:
            raise ValueError(f"Template {template_type} has no slot named {slot_id}")
        slot_bbox = _apply_slot_size_override(slot_id, template.slots[slot_id], params)
        full = _apply_safe_area(slot_bbox, safe_area)
        center_x, center_y = _norm_to_frame_center(full.cx, full.cy, frame)
        placements[object_id] = Placement(
            object_id=object_id,
            slot_id=slot_id,
            center_x=center_x,
            center_y=center_y,
            width=full.w * frame.width,
            height=full.h * frame.height,
            anchor=full.anchor,
        )
    return placements

