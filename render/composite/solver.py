from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any

from schema.composite_graph_models import CompositeGraph, GraphConstraint

from .tracks import track_point_tangent
from .types import ConstraintResidual, PartGeometry, Pose, SolveResult, anchor_world, set_center_from_anchor_target


@dataclass(frozen=True)
class SolveOptions:
    max_iters: int = 80
    tolerance: float = 1e-3


def _arg(args: dict[str, Any], *keys: str, default: Any = None) -> Any:
    for key in keys:
        if key in args:
            return args[key]
    return default


def _anchor_name(args: dict[str, Any], *keys: str, default: str = "center") -> str:
    value = _arg(args, *keys, default=default)
    return str(value or default)


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:  # noqa: BLE001
        return default


def _distance(ax: float, ay: float, bx: float, by: float) -> float:
    return math.hypot(ax - bx, ay - by)


def _part_or_raise(poses: dict[str, Pose], geoms: dict[str, PartGeometry], part_id: str, field: str) -> tuple[Pose, PartGeometry]:
    if part_id not in poses or part_id not in geoms:
        raise ValueError(f"{field} references unknown part id: {part_id}")
    return poses[part_id], geoms[part_id]


def _resolve_point_ref(
    *,
    args: dict[str, Any],
    index: int,
    poses: dict[str, Pose],
    geoms: dict[str, PartGeometry],
) -> tuple[float, float]:
    part_key = f"part_{index}"
    anchor_key = f"anchor_{index}"
    point_key = f"point_{index}"

    explicit = args.get(point_key)
    if isinstance(explicit, (list, tuple)) and len(explicit) >= 2:
        return _to_float(explicit[0]), _to_float(explicit[1])

    part_id = _arg(args, part_key, default=None)
    if isinstance(part_id, str):
        pose, geom = _part_or_raise(poses, geoms, part_id, part_key)
        local = geom.anchor_local(_anchor_name(args, anchor_key, default="center"))
        return anchor_world(pose, local)

    x = args.get(f"x{index}")
    y = args.get(f"y{index}")
    if x is not None and y is not None:
        return _to_float(x), _to_float(y)

    raise ValueError(f"Cannot resolve point_{index} from args")


def _apply_attach(
    *,
    args: dict[str, Any],
    poses: dict[str, Pose],
    geoms: dict[str, PartGeometry],
) -> float:
    part_a = str(_arg(args, "part_a", "from_part_id", "source_part_id", "part_id", default=""))
    part_b = str(_arg(args, "part_b", "to_part_id", "target_part_id", default=""))
    if not part_a or not part_b:
        raise ValueError("attach requires part_a and part_b")

    pose_a, geom_a = _part_or_raise(poses, geoms, part_a, "part_a")
    pose_b, geom_b = _part_or_raise(poses, geoms, part_b, "part_b")

    anchor_a = geom_a.anchor_local(_anchor_name(args, "anchor_a", "from_anchor", "anchor", default="center"))
    anchor_b = geom_b.anchor_local(_anchor_name(args, "anchor_b", "to_anchor", default="center"))

    ax, ay = anchor_world(pose_a, anchor_a)
    bx, by = anchor_world(pose_b, anchor_b)
    dx = bx - ax
    dy = by - ay

    mode = str(_arg(args, "mode", default="a_to_b")).lower()
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


def _apply_on_segment(
    *,
    args: dict[str, Any],
    poses: dict[str, Pose],
    geoms: dict[str, PartGeometry],
    tracks: dict[str, tuple[str, dict[str, Any]]],
) -> float:
    part_id = str(_arg(args, "part_id", default=""))
    track_id = str(_arg(args, "track_id", default=""))
    if not part_id or not track_id:
        raise ValueError("on_segment requires part_id and track_id")
    if track_id not in tracks:
        raise ValueError(f"track_id references unknown track id: {track_id}")

    pose, geom = _part_or_raise(poses, geoms, part_id, "part_id")
    anchor = geom.anchor_local(_anchor_name(args, "anchor", default="bottom_center"))

    s = _to_float(_arg(args, "t", "s", default=0.5), default=0.5)
    point, tangent = track_point_tangent(tracks[track_id][0], tracks[track_id][1], s)
    ax, ay = anchor_world(pose, anchor)
    dx = point[0] - ax
    dy = point[1] - ay
    pose.x += dx
    pose.y += dy

    orient = str(_arg(args, "orient", "theta_mode", default="none")).lower()
    if orient in {"tangent", "normal"}:
        theta = math.degrees(math.atan2(tangent[1], tangent[0]))
        if orient == "normal":
            theta += 90.0
        pose.theta = theta

    return math.hypot(dx, dy)


def _apply_midpoint(
    *,
    args: dict[str, Any],
    poses: dict[str, Pose],
    geoms: dict[str, PartGeometry],
) -> float:
    part_id = str(_arg(args, "part_id", default=""))
    if not part_id:
        raise ValueError("midpoint requires part_id")
    pose, geom = _part_or_raise(poses, geoms, part_id, "part_id")
    anchor = geom.anchor_local(_anchor_name(args, "anchor", default="center"))

    x1, y1 = _resolve_point_ref(args=args, index=1, poses=poses, geoms=geoms)
    x2, y2 = _resolve_point_ref(args=args, index=2, poses=poses, geoms=geoms)
    tx = 0.5 * (x1 + x2)
    ty = 0.5 * (y1 + y2)

    ax, ay = anchor_world(pose, anchor)
    dx = tx - ax
    dy = ty - ay
    pose.x += dx
    pose.y += dy
    return math.hypot(dx, dy)


def _apply_align_axis(
    *,
    args: dict[str, Any],
    poses: dict[str, Pose],
    geoms: dict[str, PartGeometry],
) -> float:
    part_a = str(_arg(args, "part_a", "part_id", default=""))
    part_b = str(_arg(args, "part_b", default=""))
    if not part_a or not part_b:
        raise ValueError("align_axis requires part_a and part_b")

    pose_a, geom_a = _part_or_raise(poses, geoms, part_a, "part_a")
    pose_b, geom_b = _part_or_raise(poses, geoms, part_b, "part_b")

    anchor_a = geom_a.anchor_local(_anchor_name(args, "anchor_a", "anchor", default="center"))
    anchor_b = geom_b.anchor_local(_anchor_name(args, "anchor_b", default="center"))

    ax, ay = anchor_world(pose_a, anchor_a)
    bx, by = anchor_world(pose_b, anchor_b)
    axis = str(_arg(args, "axis", default="x")).lower()
    mode = str(_arg(args, "mode", default="a_to_b")).lower()

    if axis == "y":
        diff = by - ay
        if mode == "b_to_a":
            pose_b.y -= diff
        elif mode == "both":
            pose_a.y += 0.5 * diff
            pose_b.y -= 0.5 * diff
        else:
            pose_a.y += diff
        return abs(diff)

    diff = bx - ax
    if mode == "b_to_a":
        pose_b.x -= diff
    elif mode == "both":
        pose_a.x += 0.5 * diff
        pose_b.x -= 0.5 * diff
    else:
        pose_a.x += diff
    return abs(diff)


def _apply_distance(
    *,
    args: dict[str, Any],
    poses: dict[str, Pose],
    geoms: dict[str, PartGeometry],
) -> float:
    part_a = str(_arg(args, "part_a", default=""))
    part_b = str(_arg(args, "part_b", default=""))
    if not part_a or not part_b:
        raise ValueError("distance requires part_a and part_b")
    pose_a, geom_a = _part_or_raise(poses, geoms, part_a, "part_a")
    pose_b, geom_b = _part_or_raise(poses, geoms, part_b, "part_b")

    anchor_a = geom_a.anchor_local(_anchor_name(args, "anchor_a", default="center"))
    anchor_b = geom_b.anchor_local(_anchor_name(args, "anchor_b", default="center"))
    target = _to_float(_arg(args, "d", "distance", default=0.0), default=0.0)

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
    mode = str(_arg(args, "mode", default="both")).lower()

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


def _apply_constraint(
    *,
    constraint: GraphConstraint,
    poses: dict[str, Pose],
    geoms: dict[str, PartGeometry],
    tracks: dict[str, tuple[str, dict[str, Any]]],
) -> float:
    ctype = constraint.type
    args = dict(constraint.args or {})
    if ctype == "attach":
        return _apply_attach(args=args, poses=poses, geoms=geoms)
    if ctype == "on_segment":
        return _apply_on_segment(args=args, poses=poses, geoms=geoms, tracks=tracks)
    if ctype == "midpoint":
        return _apply_midpoint(args=args, poses=poses, geoms=geoms)
    if ctype == "align_axis":
        return _apply_align_axis(args=args, poses=poses, geoms=geoms)
    if ctype == "distance":
        return _apply_distance(args=args, poses=poses, geoms=geoms)
    raise ValueError(f"Unsupported constraint type: {ctype}")


def _measure_residual(
    *,
    constraint: GraphConstraint,
    poses: dict[str, Pose],
    geoms: dict[str, PartGeometry],
    tracks: dict[str, tuple[str, dict[str, Any]]],
    tolerance: float,
) -> ConstraintResidual:
    args = dict(constraint.args or {})
    ctype = constraint.type

    if ctype == "attach":
        part_a = str(_arg(args, "part_a", "from_part_id", "source_part_id", "part_id", default=""))
        part_b = str(_arg(args, "part_b", "to_part_id", "target_part_id", default=""))
        pose_a, geom_a = _part_or_raise(poses, geoms, part_a, "part_a")
        pose_b, geom_b = _part_or_raise(poses, geoms, part_b, "part_b")
        a = anchor_world(pose_a, geom_a.anchor_local(_anchor_name(args, "anchor_a", "from_anchor", "anchor")))
        b = anchor_world(pose_b, geom_b.anchor_local(_anchor_name(args, "anchor_b", "to_anchor")))
        residual = _distance(a[0], a[1], b[0], b[1])
        return ConstraintResidual(constraint.id, ctype, residual, constraint.hard, residual <= tolerance, "")

    if ctype == "on_segment":
        part_id = str(_arg(args, "part_id", default=""))
        track_id = str(_arg(args, "track_id", default=""))
        pose, geom = _part_or_raise(poses, geoms, part_id, "part_id")
        if track_id not in tracks:
            raise ValueError(f"track_id references unknown track id: {track_id}")
        s = _to_float(_arg(args, "t", "s", default=0.5), default=0.5)
        target, _ = track_point_tangent(tracks[track_id][0], tracks[track_id][1], s)
        point = anchor_world(pose, geom.anchor_local(_anchor_name(args, "anchor", default="bottom_center")))
        residual = _distance(point[0], point[1], target[0], target[1])
        return ConstraintResidual(constraint.id, ctype, residual, constraint.hard, residual <= tolerance, "")

    if ctype == "midpoint":
        part_id = str(_arg(args, "part_id", default=""))
        pose, geom = _part_or_raise(poses, geoms, part_id, "part_id")
        target1 = _resolve_point_ref(args=args, index=1, poses=poses, geoms=geoms)
        target2 = _resolve_point_ref(args=args, index=2, poses=poses, geoms=geoms)
        mx = 0.5 * (target1[0] + target2[0])
        my = 0.5 * (target1[1] + target2[1])
        point = anchor_world(pose, geom.anchor_local(_anchor_name(args, "anchor", default="center")))
        residual = _distance(point[0], point[1], mx, my)
        return ConstraintResidual(constraint.id, ctype, residual, constraint.hard, residual <= tolerance, "")

    if ctype == "align_axis":
        part_a = str(_arg(args, "part_a", "part_id", default=""))
        part_b = str(_arg(args, "part_b", default=""))
        pose_a, geom_a = _part_or_raise(poses, geoms, part_a, "part_a")
        pose_b, geom_b = _part_or_raise(poses, geoms, part_b, "part_b")
        a = anchor_world(pose_a, geom_a.anchor_local(_anchor_name(args, "anchor_a", "anchor", default="center")))
        b = anchor_world(pose_b, geom_b.anchor_local(_anchor_name(args, "anchor_b", default="center")))
        axis = str(_arg(args, "axis", default="x")).lower()
        residual = abs((b[1] - a[1]) if axis == "y" else (b[0] - a[0]))
        return ConstraintResidual(constraint.id, ctype, residual, constraint.hard, residual <= tolerance, "")

    if ctype == "distance":
        part_a = str(_arg(args, "part_a", default=""))
        part_b = str(_arg(args, "part_b", default=""))
        pose_a, geom_a = _part_or_raise(poses, geoms, part_a, "part_a")
        pose_b, geom_b = _part_or_raise(poses, geoms, part_b, "part_b")
        a = anchor_world(pose_a, geom_a.anchor_local(_anchor_name(args, "anchor_a", default="center")))
        b = anchor_world(pose_b, geom_b.anchor_local(_anchor_name(args, "anchor_b", default="center")))
        target = _to_float(_arg(args, "d", "distance", default=0.0), default=0.0)
        residual = abs(_distance(a[0], a[1], b[0], b[1]) - target)
        return ConstraintResidual(constraint.id, ctype, residual, constraint.hard, residual <= tolerance, "")

    raise ValueError(f"Unsupported constraint type: {ctype}")


def solve_static(
    graph: CompositeGraph,
    *,
    geometries: dict[str, PartGeometry],
    options: SolveOptions | None = None,
) -> SolveResult:
    opts = options or SolveOptions()
    poses = {
        part.id: Pose(
            x=float(part.seed_pose.x),
            y=float(part.seed_pose.y),
            theta=float(part.seed_pose.theta),
            scale=float(part.seed_pose.scale),
            z=float(part.seed_pose.z),
        )
        for part in graph.parts
    }
    tracks = {track.id: (track.type, dict(track.data or {})) for track in graph.tracks}

    converged = False
    for _ in range(max(1, opts.max_iters)):
        max_residual = 0.0
        for constraint in graph.constraints:
            residual = _apply_constraint(constraint=constraint, poses=poses, geoms=geometries, tracks=tracks)
            if residual > max_residual:
                max_residual = residual
        if max_residual <= opts.tolerance:
            converged = True
            break

    residuals = [
        _measure_residual(
            constraint=constraint,
            poses=poses,
            geoms=geometries,
            tracks=tracks,
            tolerance=opts.tolerance,
        )
        for constraint in graph.constraints
    ]
    if not converged:
        converged = all(item.satisfied for item in residuals if item.hard)
    return SolveResult(poses=poses, residuals=residuals, converged=converged)
