from __future__ import annotations

import math

from render.composite.tracks import track_point_tangent
from render.composite.types import PartGeometry, Pose, anchor_world, set_center_from_anchor_target

from .common import anchor_name, arg, part_or_raise, to_float


def _resolve_target_theta(*, angle_mode: str, args: dict, pose: Pose, tangent: tuple[float, float]) -> float:
    offset = to_float(args.get("angle_offset", 0.0), default=0.0)
    mode = (angle_mode or "tangent").strip().lower()
    if mode == "keep":
        return float(pose.theta) + offset
    if mode == "fixed":
        return to_float(args.get("angle", pose.theta), default=float(pose.theta)) + offset
    base = math.degrees(math.atan2(tangent[1], tangent[0]))
    if mode == "normal":
        base += 90.0
    return base + offset


def apply(
    *,
    args: dict,
    poses: dict[str, Pose],
    geoms: dict[str, PartGeometry],
    tracks: dict[str, tuple[str, dict]],
) -> float:
    part_id = str(arg(args, "part_id", default=""))
    track_id = str(arg(args, "track_id", default=""))
    if not part_id or not track_id:
        raise ValueError("on_track_pose requires part_id and track_id")
    if track_id not in tracks:
        raise ValueError(f"track_id references unknown track id: {track_id}")

    pose, geom = part_or_raise(poses, geoms, part_id, "part_id")
    local_anchor = geom.anchor_local(anchor_name(args, "anchor", default="bottom_center"))

    s = to_float(arg(args, "t", "s", default=0.0), default=0.0)
    track_type, track_data = tracks[track_id]

    # Dynamic tracks: allow line/segment tracks to reference another part's
    # anchors so blocks can stay attached even after the solver moves/rotates
    # the track-defining part.
    #
    # Example track data:
    #   {"part_id": "p_incline", "anchor_a": "start", "anchor_b": "end"}
    if isinstance(track_data, dict) and (track_type or "").strip().lower() in {"line", "segment"}:
        ref_part_id = track_data.get("part_id")
        if isinstance(ref_part_id, str) and ref_part_id:
            ref_pose, ref_geom = part_or_raise(poses, geoms, ref_part_id, "track.part_id")
            a_name = str(track_data.get("anchor_a") or "start")
            b_name = str(track_data.get("anchor_b") or "end")
            a_local = ref_geom.anchor_local(a_name)
            b_local = ref_geom.anchor_local(b_name)
            ax, ay = anchor_world(ref_pose, a_local)
            bx, by = anchor_world(ref_pose, b_local)
            track_data = dict(track_data)
            track_data["x1"] = float(ax)
            track_data["y1"] = float(ay)
            track_data["x2"] = float(bx)
            track_data["y2"] = float(by)

    point, tangent = track_point_tangent(track_type, track_data, s)
    angle_mode = str(arg(args, "angle_mode", default="tangent"))
    pose.theta = _resolve_target_theta(angle_mode=angle_mode, args=args, pose=pose, tangent=tangent)
    target = (point[0], point[1])
    set_center_from_anchor_target(pose, local_anchor, target_x=float(target[0]), target_y=float(target[1]))

    world_anchor = anchor_world(pose, local_anchor)
    return math.hypot(world_anchor[0] - target[0], world_anchor[1] - target[1])


def measure(
    *,
    args: dict,
    poses: dict[str, Pose],
    geoms: dict[str, PartGeometry],
    tracks: dict[str, tuple[str, dict]],
) -> float:
    part_id = str(arg(args, "part_id", default=""))
    track_id = str(arg(args, "track_id", default=""))
    pose, geom = part_or_raise(poses, geoms, part_id, "part_id")
    if track_id not in tracks:
        raise ValueError(f"track_id references unknown track id: {track_id}")

    local_anchor = geom.anchor_local(anchor_name(args, "anchor", default="bottom_center"))
    s = to_float(arg(args, "t", "s", default=0.0), default=0.0)
    track_type, track_data = tracks[track_id]

    if isinstance(track_data, dict) and (track_type or "").strip().lower() in {"line", "segment"}:
        ref_part_id = track_data.get("part_id")
        if isinstance(ref_part_id, str) and ref_part_id:
            ref_pose, ref_geom = part_or_raise(poses, geoms, ref_part_id, "track.part_id")
            a_name = str(track_data.get("anchor_a") or "start")
            b_name = str(track_data.get("anchor_b") or "end")
            a_local = ref_geom.anchor_local(a_name)
            b_local = ref_geom.anchor_local(b_name)
            ax, ay = anchor_world(ref_pose, a_local)
            bx, by = anchor_world(ref_pose, b_local)
            track_data = dict(track_data)
            track_data["x1"] = float(ax)
            track_data["y1"] = float(ay)
            track_data["x2"] = float(bx)
            track_data["y2"] = float(by)

    point, tangent = track_point_tangent(track_type, track_data, s)
    target = (point[0], point[1])
    world_anchor = anchor_world(pose, local_anchor)
    return math.hypot(world_anchor[0] - target[0], world_anchor[1] - target[1])
