from __future__ import annotations

from typing import Any

from .common import _to_float


def _timeline_points(timeline: list[dict[str, Any]], *, key: str) -> list[tuple[float, float]]:
    points = sorted(
        [
            (float(item.get("t", 0.0)), _to_float(item.get(key, 0.0)))
            for item in timeline
            if isinstance(item, dict)
        ],
        key=lambda x: x[0],
    )
    return points


def evaluate_timeline(timeline: list[dict[str, Any]], time_value: float, *, key: str = "s") -> float:
    if not timeline:
        return 0.0
    points = _timeline_points(timeline, key=key)
    if not points:
        return 0.0

    t = float(time_value)
    if t <= points[0][0]:
        return points[0][1]
    if t >= points[-1][0]:
        return points[-1][1]

    for index in range(1, len(points)):
        t0, v0 = points[index - 1]
        t1, v1 = points[index]
        if t0 <= t <= t1:
            if abs(t1 - t0) <= 1e-9:
                return v1
            alpha = (t - t0) / (t1 - t0)
            return v0 + (v1 - v0) * alpha
    return points[-1][1]


def timeline_bounds(timeline: list[dict[str, Any]]) -> tuple[float, float] | None:
    points = _timeline_points(timeline, key="t")
    if not points:
        return None
    return points[0][0], points[-1][0]


__all__ = [
    "evaluate_timeline",
    "timeline_bounds",
]
