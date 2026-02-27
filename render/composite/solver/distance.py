from __future__ import annotations

import math

from render.composite.types import PartGeometry, Pose, anchor_world

from .common import anchor_name, arg, part_or_raise, to_float


def apply(*, args: dict, poses: dict[str, Pose], geoms: dict[str, PartGeometry]) -> float:
    part_a = str(arg(args, "part_a", default=""))
    part_b = str(arg(args, "part_b", default=""))
    if not part_a or not part_b:
        raise ValueError("distance requires part_a and part_b")
    pose_a, geom_a = part_or_raise(poses, geoms, part_a, "part_a")
    pose_b, geom_b = part_or_raise(poses, geoms, part_b, "part_b")

    anchor_a = geom_a.anchor_local(anchor_name(args, "anchor_a", default="center"))
    anchor_b = geom_b.anchor_local(anchor_name(args, "anchor_b", default="center"))
    target = to_float(arg(args, "d", "distance", default=0.0), default=0.0)

    ax, ay = anchor_world(pose_a, anchor_a)
    bx, by = anchor_world(pose_b, anchor_b)
    vx = bx - ax
    vy = by - ay
    length = math.hypot(vx, vy)
    if length <= 1e-9:
        ux, uy = 1.0, 0.0
    else:
        ux, uy = vx / length, vy / length
    err = target - length
    mode = str(arg(args, "mode", default="both")).lower()

    if mode == "a_to_b":
        pose_b.x += ux * err
        pose_b.y += uy * err
    elif mode == "b_to_a":
        pose_a.x -= ux * err
        pose_a.y -= uy * err
    else:
        shift_x = 0.5 * ux * err
        shift_y = 0.5 * uy * err
        pose_a.x -= shift_x
        pose_a.y -= shift_y
        pose_b.x += shift_x
        pose_b.y += shift_y

    return abs(err)


def measure(*, args: dict, poses: dict[str, Pose], geoms: dict[str, PartGeometry]) -> float:
    part_a = str(arg(args, "part_a", default=""))
    part_b = str(arg(args, "part_b", default=""))
    pose_a, geom_a = part_or_raise(poses, geoms, part_a, "part_a")
    pose_b, geom_b = part_or_raise(poses, geoms, part_b, "part_b")
    a = anchor_world(pose_a, geom_a.anchor_local(anchor_name(args, "anchor_a", default="center")))
    b = anchor_world(pose_b, geom_b.anchor_local(anchor_name(args, "anchor_b", default="center")))
    target = to_float(arg(args, "d", "distance", default=0.0), default=0.0)
    return abs(math.hypot(a[0] - b[0], a[1] - b[1]) - target)

