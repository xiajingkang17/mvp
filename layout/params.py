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


def default_params(template_type: str) -> dict[str, float | list[float]]:
    if template_type == "left_right":
        return {"left_ratio": 0.5}
    if template_type == "hero_side":
        return {"hero_ratio": 0.66}
    if template_type == "left3_right3":
        return {"row_weights": [1.0 / 3.0] * 3}
    if template_type == "left4_right4":
        return {"row_weights": [0.25] * 4}
    return {}


def sanitize_params(template_type: str, params: dict | None) -> dict[str, float | list[float]]:
    if not isinstance(params, dict):
        return default_params(template_type)

    if template_type == "left_right":
        if "left_ratio" not in params:
            return default_params(template_type)
        try:
            left_ratio = float(params.get("left_ratio", 0.5))
        except (TypeError, ValueError):
            return default_params(template_type)
        return {"left_ratio": clamp(left_ratio, 0.3, 0.7)}

    if template_type == "hero_side":
        hero_ratio = params.get("hero_ratio", None)
        side_ratio = params.get("side_ratio", None)
        if hero_ratio is None and side_ratio is not None:
            try:
                hero_ratio = 1.0 - float(side_ratio)
            except (TypeError, ValueError):
                hero_ratio = None
        if hero_ratio is None:
            return default_params(template_type)
        try:
            hero_ratio = float(hero_ratio)
        except (TypeError, ValueError):
            return default_params(template_type)
        return {"hero_ratio": clamp(hero_ratio, 0.5, 0.8)}

    if template_type == "left3_right3":
        weights = params.get("row_weights")
        if not isinstance(weights, list) or len(weights) != 3:
            return default_params(template_type)
        try:
            return {"row_weights": normalize_weights(weights)}
        except (TypeError, ValueError):
            return default_params(template_type)

    if template_type == "left4_right4":
        weights = params.get("row_weights")
        if not isinstance(weights, list) or len(weights) != 4:
            return default_params(template_type)
        try:
            return {"row_weights": normalize_weights(weights)}
        except (TypeError, ValueError):
            return default_params(template_type)

    return {}

