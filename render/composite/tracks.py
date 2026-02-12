from __future__ import annotations

import math
from typing import Any


def _clamp01(value: float) -> float:
    if value < 0.0:
        return 0.0
    if value > 1.0:
        return 1.0
    return value


def _norm(x: float, y: float) -> tuple[float, float]:
    length = math.hypot(x, y)
    if length <= 1e-9:
        return 1.0, 0.0
    return x / length, y / length


def _segment_point_tangent(data: dict[str, Any], s: float) -> tuple[tuple[float, float], tuple[float, float]]:
    x1 = float(data.get("x1", 0.0))
    y1 = float(data.get("y1", 0.0))
    x2 = float(data.get("x2", 1.0))
    y2 = float(data.get("y2", 0.0))
    t = _clamp01(float(s))
    px = x1 + (x2 - x1) * t
    py = y1 + (y2 - y1) * t
    tx, ty = _norm(x2 - x1, y2 - y1)
    return (px, py), (tx, ty)


def _line_point_tangent(data: dict[str, Any], s: float) -> tuple[tuple[float, float], tuple[float, float]]:
    if {"x1", "y1", "x2", "y2"}.issubset(data):
        x1 = float(data.get("x1", 0.0))
        y1 = float(data.get("y1", 0.0))
        x2 = float(data.get("x2", 1.0))
        y2 = float(data.get("y2", 0.0))
        dx = x2 - x1
        dy = y2 - y1
        px = x1 + float(s) * dx
        py = y1 + float(s) * dy
        tx, ty = _norm(dx, dy)
        return (px, py), (tx, ty)

    px = float(data.get("x0", 0.0))
    py = float(data.get("y0", 0.0))
    dx = float(data.get("dx", 1.0))
    dy = float(data.get("dy", 0.0))
    tx, ty = _norm(dx, dy)
    return (px + float(s) * dx, py + float(s) * dy), (tx, ty)


def _arc_point_tangent(data: dict[str, Any], s: float) -> tuple[tuple[float, float], tuple[float, float]]:
    cx = float(data.get("cx", 0.0))
    cy = float(data.get("cy", 0.0))
    radius = float(data.get("r", data.get("radius", 1.0)))
    start_deg = float(data.get("start_deg", 0.0))
    end_deg = float(data.get("end_deg", 180.0))
    t = _clamp01(float(s))
    angle_deg = start_deg + (end_deg - start_deg) * t
    angle_rad = math.radians(angle_deg)
    px = cx + radius * math.cos(angle_rad)
    py = cy + radius * math.sin(angle_rad)

    # Tangent direction for increasing angle.
    tx = -math.sin(angle_rad)
    ty = math.cos(angle_rad)
    tx, ty = _norm(tx, ty)
    return (px, py), (tx, ty)


def track_point_tangent(track_type: str, data: dict[str, Any], s: float) -> tuple[tuple[float, float], tuple[float, float]]:
    t = (track_type or "").strip().lower()
    if t == "segment":
        return _segment_point_tangent(data, s)
    if t == "line":
        return _line_point_tangent(data, s)
    if t == "arc":
        return _arc_point_tangent(data, s)
    raise ValueError(f"Unsupported track type: {track_type}")
