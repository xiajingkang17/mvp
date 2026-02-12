from __future__ import annotations

from typing import Iterable


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def normalize_weights(weights: Iterable[float], *, min_value: float = 1e-6) -> list[float]:
    values = [max(float(w), min_value) for w in weights]
    total = sum(values)
    if total <= 0:
        count = len(values)
        return [1.0 / count] * count if count else []
    return [w / total for w in values]


def _sanitize_slot_scales(raw: object) -> dict[str, dict[str, float]]:
    if not isinstance(raw, dict):
        return {}

    cleaned: dict[str, dict[str, float]] = {}
    for raw_slot_id, raw_item in raw.items():
        slot_id = str(raw_slot_id).strip()
        if not slot_id or not isinstance(raw_item, dict):
            continue

        w_raw = raw_item.get("w", raw_item.get("width", 1.0))
        h_raw = raw_item.get("h", raw_item.get("height", 1.0))
        try:
            w = clamp(float(w_raw), 0.2, 1.0)
            h = clamp(float(h_raw), 0.2, 1.0)
        except (TypeError, ValueError):
            continue

        cleaned[slot_id] = {"w": w, "h": h}
    return cleaned


def default_params(template_type: str) -> dict[str, object]:
    _ = template_type
    return {}


def sanitize_params(template_type: str, params: dict | None) -> dict[str, object]:
    _ = template_type
    if not isinstance(params, dict):
        return {}

    slot_scales = _sanitize_slot_scales(params.get("slot_scales"))
    if not slot_scales:
        return {}
    return {"slot_scales": slot_scales}
