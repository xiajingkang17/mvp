from __future__ import annotations

import math

from render.composite.types import PartGeometry, Pose, anchor_world

from .common import anchor_name, arg, part_or_raise, resolve_point_ref


def apply(*, args: dict, poses: dict[str, Pose], geoms: dict[str, PartGeometry]) -> float:
    part_id = str(arg(args, "part_id", default=""))
    if not part_id:
        raise ValueError("midpoint requires part_id")
    pose, geom = part_or_raise(poses, geoms, part_id, "part_id")
    anchor = geom.anchor_local(anchor_name(args, "anchor", default="center"))

    x1, y1 = resolve_point_ref(args=args, index=1, poses=poses, geoms=geoms)
    x2, y2 = resolve_point_ref(args=args, index=2, poses=poses, geoms=geoms)
    tx = 0.5 * (x1 + x2)
    ty = 0.5 * (y1 + y2)

    ax, ay = anchor_world(pose, anchor)
    dx = tx - ax
    dy = ty - ay
    pose.x += dx
    pose.y += dy
    return math.hypot(dx, dy)


def measure(*, args: dict, poses: dict[str, Pose], geoms: dict[str, PartGeometry]) -> float:
    part_id = str(arg(args, "part_id", default=""))
    pose, geom = part_or_raise(poses, geoms, part_id, "part_id")
    target1 = resolve_point_ref(args=args, index=1, poses=poses, geoms=geoms)
    target2 = resolve_point_ref(args=args, index=2, poses=poses, geoms=geoms)
    mx = 0.5 * (target1[0] + target2[0])
    my = 0.5 * (target1[1] + target2[1])
    point = anchor_world(pose, geom.anchor_local(anchor_name(args, "anchor", default="center")))
    return math.hypot(point[0] - mx, point[1] - my)

