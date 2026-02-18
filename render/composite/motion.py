from __future__ import annotations

from typing import Any

from schema.composite_graph_models import CompositeGraph, GraphMotion

from .solver.on_track_pose import apply as apply_on_track_pose
from .types import PartGeometry, Pose
# from .pymunk_motion import PymunkNotAvailable, precompute_timeline

_POSE_ARG_KEYS = (
    "anchor",
    "contact_side",
    "angle_mode",
    "angle",
    "angle_offset",
    "clearance",
)


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

    s = evaluate_timeline(motion.timeline, time_value, key=str(_arg(args, "param_key", default="s")))
    pose_args = dict(args)
    pose_args["part_id"] = part_id
    pose_args["track_id"] = track_id
    pose_args["s"] = float(s)
    if "angle_mode" not in pose_args and ("theta_mode" in pose_args or "orient" in pose_args):
        pose_args["angle_mode"] = str(_arg(pose_args, "theta_mode", "orient", default="keep"))
    apply_on_track_pose(args=pose_args, poses=poses, geoms=geometries, tracks=tracks)


def _pick_schedule_segment(
    segments: list[dict[str, Any]],
    u_value: float,
) -> tuple[dict[str, Any], str, float] | None:
    prepared: list[tuple[float, float, float, float, str, int, dict[str, Any]]] = []
    for index, raw in enumerate(segments):
        if not isinstance(raw, dict):
            continue
        segment = dict(raw)
        track_id = str(raw.get("track_id", "")).strip()
        if not track_id:
            continue
        u0 = _to_float(raw.get("u0", raw.get("from_u", 0.0)), default=0.0)
        u1 = _to_float(raw.get("u1", raw.get("to_u", u0)), default=u0)
        s0 = _to_float(raw.get("s0", raw.get("from_s", 0.0)), default=0.0)
        s1 = _to_float(raw.get("s1", raw.get("to_s", 1.0)), default=1.0)
        if u1 < u0:
            u0, u1 = u1, u0
            s0, s1 = s1, s0
        prepared.append((u0, u1, s0, s1, track_id, index, segment))

    if not prepared:
        return None
    prepared.sort(key=lambda item: (item[0], item[1], item[5]))

    chosen = prepared[0]
    if u_value <= prepared[0][0]:
        chosen = prepared[0]
    elif u_value >= prepared[-1][1]:
        chosen = prepared[-1]
    else:
        for item in prepared:
            if item[0] <= u_value <= item[1]:
                chosen = item
                break

    u0, u1, s0, s1, track_id, _, segment = chosen
    if abs(u1 - u0) <= 1e-9:
        alpha = 1.0
    else:
        alpha = (u_value - u0) / (u1 - u0)
    if alpha < 0.0:
        alpha = 0.0
    if alpha > 1.0:
        alpha = 1.0
    s_value = s0 + (s1 - s0) * alpha
    return segment, track_id, s_value


def _apply_on_track_schedule(
    *,
    motion: GraphMotion,
    poses: dict[str, Pose],
    geometries: dict[str, PartGeometry],
    tracks: dict[str, tuple[str, dict[str, Any]]],
    time_value: float,
) -> None:
    args = dict(motion.args or {})
    part_id = str(_arg(args, "part_id", default=""))
    if not part_id or part_id not in poses or part_id not in geometries:
        return

    segments = args.get("segments")
    if not isinstance(segments, list) or not segments:
        return

    u_value = evaluate_timeline(motion.timeline, time_value, key=str(_arg(args, "param_key", default="u")))
    picked = _pick_schedule_segment(segments, u_value)
    if picked is None:
        return
    segment, track_id, s_value = picked
    if track_id not in tracks:
        return

    pose_args = dict(args)
    for key in _POSE_ARG_KEYS:
        if key in segment:
            pose_args[key] = segment[key]
    pose_args["part_id"] = part_id
    pose_args["track_id"] = track_id
    pose_args["s"] = float(s_value)
    if "angle_mode" not in pose_args and ("theta_mode" in pose_args or "orient" in pose_args):
        pose_args["angle_mode"] = str(_arg(pose_args, "theta_mode", "orient", default="keep"))
    apply_on_track_pose(args=pose_args, poses=poses, geoms=geometries, tracks=tracks)


def resolve_motion_pose_args(
    graph: CompositeGraph,
    *,
    time_value: float = 0.0,
) -> list[dict[str, Any]]:
    tracks = {track.id: (track.type, dict(track.data or {})) for track in graph.tracks}
    resolved: list[dict[str, Any]] = []

    for motion in graph.motions:
        args = dict(motion.args or {})
        part_id = str(_arg(args, "part_id", default="")).strip()
        if not part_id:
            continue

        if motion.type == "on_track":
            track_id = str(_arg(args, "track_id", default="")).strip()
            if not track_id or track_id not in tracks:
                continue

            s = evaluate_timeline(motion.timeline, time_value, key=str(_arg(args, "param_key", default="s")))
            pose_args: dict[str, Any] = {"part_id": part_id, "track_id": track_id, "s": float(s)}
            for key in _POSE_ARG_KEYS:
                if key in args:
                    pose_args[key] = args[key]
            if "angle_mode" not in pose_args and ("theta_mode" in args or "orient" in args):
                pose_args["angle_mode"] = str(_arg(args, "theta_mode", "orient", default="keep"))
            resolved.append(pose_args)
            continue

        if motion.type != "on_track_schedule":
            continue

        segments = args.get("segments")
        if not isinstance(segments, list) or not segments:
            continue
        u_value = evaluate_timeline(motion.timeline, time_value, key=str(_arg(args, "param_key", default="u")))
        picked = _pick_schedule_segment(segments, u_value)
        if picked is None:
            continue

        segment, track_id, s_value = picked
        if track_id not in tracks:
            continue

        pose_args = {"part_id": part_id, "track_id": track_id, "s": float(s_value)}
        for key in _POSE_ARG_KEYS:
            if key in args:
                pose_args[key] = args[key]
            if key in segment:
                pose_args[key] = segment[key]
        if "angle_mode" not in pose_args and ("theta_mode" in args or "orient" in args):
            pose_args["angle_mode"] = str(_arg(args, "theta_mode", "orient", default="keep"))
        resolved.append(pose_args)

    return resolved

# def _apply_pymunk_body(
#     *,
#     motion: GraphMotion,
#     poses: dict[str, Pose],
#     geometries: dict[str, PartGeometry],
#     time_value: float,
# ) -> None:
#     args = dict(motion.args or {})
#     part_id = str(_arg(args, "part_id", default=""))
#     if not part_id or part_id not in poses or part_id not in geometries:
#         return
#
#     # Precompute/cached dense timeline once, then interpolate per-frame.
#     if not motion.timeline:
#         try:
#             motion.timeline = precompute_timeline(motion)  # type: ignore[assignment]
#         except PymunkNotAvailable:
#             raise
#
#     if not motion.timeline:
#         return
#
#     pose = poses[part_id]
#     pose.x = evaluate_timeline(motion.timeline, time_value, key="x")
#     pose.y = evaluate_timeline(motion.timeline, time_value, key="y")
#     pose.theta = evaluate_timeline(motion.timeline, time_value, key="theta")


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
        elif motion.type == "on_track_schedule":
            _apply_on_track_schedule(
                motion=motion,
                poses=updated,
                geometries=geometries,
                tracks=tracks,
                time_value=time_value,
            )
        # elif motion.type == "pymunk_body":
        #     _apply_pymunk_body(
        #         motion=motion,
        #         poses=updated,
        #         geometries=geometries,
        #         time_value=time_value,
        #     )
    return updated
