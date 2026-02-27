from __future__ import annotations

import math

from render.composite.types import PartGeometry, Pose, anchor_world

from .common import anchor_name, arg, part_or_raise


def apply(*, args: dict, poses: dict[str, Pose], geoms: dict[str, PartGeometry]) -> float:
    part_a = str(arg(args, "part_a", "from_part_id", "source_part_id", "part_id", default=""))
    part_b = str(arg(args, "part_b", "to_part_id", "target_part_id", default=""))
    if not part_a or not part_b:
        raise ValueError("attach requires part_a and part_b")

    pose_a, geom_a = part_or_raise(poses, geoms, part_a, "part_a")
    pose_b, geom_b = part_or_raise(poses, geoms, part_b, "part_b")

    local_anchor_a = geom_a.anchor_local(anchor_name(args, "anchor_a", "from_anchor", "anchor", default="center"))
    local_anchor_b = geom_b.anchor_local(anchor_name(args, "anchor_b", "to_anchor", default="center"))

    ax, ay = anchor_world(pose_a, local_anchor_a)
    bx, by = anchor_world(pose_b, local_anchor_b)
    dx = bx - ax
    dy = by - ay

    mode = str(arg(args, "mode", default="a_to_b")).lower()
    if mode == "b_to_a":
        pose_b.x -= dx
        pose_b.y -= dy
    elif mode == "both":
        pose_a.x += 0.5 * dx
        pose_a.y += 0.5 * dy
        pose_b.x -= 0.5 * dx
        pose_b.y -= 0.5 * dy
    else:
        pose_a.x += dx
        pose_a.y += dy

    return math.hypot(dx, dy)


def measure(*, args: dict, poses: dict[str, Pose], geoms: dict[str, PartGeometry]) -> float:
    part_a = str(arg(args, "part_a", "from_part_id", "source_part_id", "part_id", default=""))
    part_b = str(arg(args, "part_b", "to_part_id", "target_part_id", default=""))
    pose_a, geom_a = part_or_raise(poses, geoms, part_a, "part_a")
    pose_b, geom_b = part_or_raise(poses, geoms, part_b, "part_b")
    anchor_a = geom_a.anchor_local(anchor_name(args, "anchor_a", "from_anchor", "anchor"))
    anchor_b = geom_b.anchor_local(anchor_name(args, "anchor_b", "to_anchor"))
    a = anchor_world(pose_a, anchor_a)
    b = anchor_world(pose_b, anchor_b)
    return math.hypot(a[0] - b[0], a[1] - b[1])

