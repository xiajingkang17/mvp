from __future__ import annotations

import math
from typing import Any

from schema.composite_graph_models import CompositeGraph, GraphMotion

from .tracks import track_point_tangent
from .types import PartGeometry, Pose, set_center_from_anchor_target


def _arg(args: dict[str, Any], *keys: str, default: Any = None) -> Any:
    for key in keys:
        if key in args:
            return args[key]
    return default


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:  # noqa: BLE001
        return default


def evaluate_timeline(timeline: list[dict[str, Any]], time_value: float, *, key: str = "s") -> float:
    if not timeline:
        return 0.0
    points = sorted(
        [
            (float(item.get("t", 0.0)), _to_float(item.get(key, 0.0)))
            for item in timeline
            if isinstance(item, dict)
        ],
        key=lambda x: x[0],
    )
    if not points:
        return 0.0

    t = float(time_value)
    if t <= points[0][0]:
        return points[0][1]
    if t >= points[-1][0]:
        return points[-1][1]

    for i in range(1, len(points)):
        t0, v0 = points[i - 1]
        t1, v1 = points[i]
        if t0 <= t <= t1:
            if abs(t1 - t0) <= 1e-9:
                return v1
            alpha = (t - t0) / (t1 - t0)
            return v0 + (v1 - v0) * alpha
    return points[-1][1]


def _apply_on_track(
    *,
    motion: GraphMotion,
    poses: dict[str, Pose],
    geometries: dict[str, PartGeometry],
    tracks: dict[str, tuple[str, dict[str, Any]]],
    time_value: float,
) -> None:
    args = dict(motion.args or {})
    part_id = str(_arg(args, "part_id", default=""))
    track_id = str(_arg(args, "track_id", default=""))
    if not part_id or part_id not in poses or part_id not in geometries:
        return
    if not track_id or track_id not in tracks:
        return

    pose = poses[part_id]
    geom = geometries[part_id]
    anchor_name = str(_arg(args, "anchor", default="bottom_center"))
    local_anchor = geom.anchor_local(anchor_name)

    s = evaluate_timeline(motion.timeline, time_value, key=str(_arg(args, "param_key", default="s")))
    target, tangent = track_point_tangent(tracks[track_id][0], tracks[track_id][1], s)

    theta_mode = str(_arg(args, "theta_mode", "orient", default="keep")).lower()
    if theta_mode in {"tangent", "normal"}:
        theta = math.degrees(math.atan2(tangent[1], tangent[0]))
        if theta_mode == "normal":
            theta += 90.0
        pose.theta = theta

    set_center_from_anchor_target(
        pose,
        local_anchor,
        target_x=float(target[0]),
        target_y=float(target[1]),
    )


def apply_motions(
    graph: CompositeGraph,
    *,
    poses: dict[str, Pose],
    geometries: dict[str, PartGeometry],
    time_value: float = 0.0,
) -> dict[str, Pose]:
    updated = {part_id: pose.copy() for part_id, pose in poses.items()}
    tracks = {track.id: (track.type, dict(track.data or {})) for track in graph.tracks}
    for motion in graph.motions:
        if motion.type == "on_track":
            _apply_on_track(
                motion=motion,
                poses=updated,
                geometries=geometries,
                tracks=tracks,
                time_value=time_value,
            )
    return updated
