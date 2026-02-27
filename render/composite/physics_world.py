from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from schema.composite_graph_models import CompositeGraph, GraphMotion

from .motion import evaluate_timeline, timeline_bounds
from .types import PartGeometry, Pose, anchor_world


class PhysicsWorldNotAvailable(RuntimeError):
    pass


@dataclass(frozen=True)
class PhysicsWorldResult:
    motion_id: str
    param_key: str
    tau_start: float
    tau_end: float
    samples_by_part: dict[str, list[dict[str, float]]]
    collision_events: list[dict[str, Any]]


def _to_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except Exception:  # noqa: BLE001
        return float(default)


def _to_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except Exception:  # noqa: BLE001
        return int(default)


def _to_bool(value: Any, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "y", "on"}:
        return True
    if text in {"0", "false", "no", "n", "off"}:
        return False
    return default


def _parse_gravity(value: Any) -> tuple[float, float]:
    if isinstance(value, (list, tuple)) and len(value) >= 2:
        try:
            return float(value[0]), float(value[1])
        except Exception:  # noqa: BLE001
            pass
    return 0.0, -9.8


def _geometry_size(geom: PartGeometry, *, default_width: float = 0.8, default_height: float = 0.5) -> tuple[float, float]:
    if not geom.anchors:
        return float(default_width), float(default_height)
    xs = [float(point[0]) for point in geom.anchors.values()]
    ys = [float(point[1]) for point in geom.anchors.values()]
    if not xs or not ys:
        return float(default_width), float(default_height)
    width = max(xs) - min(xs)
    height = max(ys) - min(ys)
    if abs(width) <= 1e-6:
        width = float(default_width)
    if abs(height) <= 1e-6:
        height = float(default_height)
    return abs(float(width)), abs(float(height))


def _track_data_to_world(
    *,
    track_type: str,
    track_data: dict[str, Any],
    poses: dict[str, Pose],
    geoms: dict[str, PartGeometry],
) -> dict[str, Any]:
    out = dict(track_data or {})
    if track_type not in {"line", "segment"}:
        return out
    ref_part_id = out.get("part_id")
    if not isinstance(ref_part_id, str) or not ref_part_id.strip():
        return out
    ref_part_id = ref_part_id.strip()
    if ref_part_id not in poses or ref_part_id not in geoms:
        return out
    try:
        ref_geom = geoms[ref_part_id]
        a_name = str(out.get("anchor_a") or out.get("a1") or "start")
        b_name = str(out.get("anchor_b") or out.get("a2") or "end")
        a_local = ref_geom.anchor_local(a_name)
        b_local = ref_geom.anchor_local(b_name)
        ax, ay = anchor_world(poses[ref_part_id], a_local)
        bx, by = anchor_world(poses[ref_part_id], b_local)
    except Exception:  # noqa: BLE001
        return out
    out["x1"] = float(ax)
    out["y1"] = float(ay)
    out["x2"] = float(bx)
    out["y2"] = float(by)
    return out


def _segment_from_track(
    *,
    track_type: str,
    track_data: dict[str, Any],
    graph: CompositeGraph,
) -> tuple[float, float, float, float] | None:
    ttype = str(track_type).strip().lower()
    if ttype not in {"line", "segment"}:
        return None

    if {"x1", "y1", "x2", "y2"}.issubset(track_data):
        return (
            float(track_data["x1"]),
            float(track_data["y1"]),
            float(track_data["x2"]),
            float(track_data["y2"]),
        )

    if {"x0", "y0", "dx", "dy"}.issubset(track_data):
        x0 = float(track_data["x0"])
        y0 = float(track_data["y0"])
        dx = float(track_data["dx"])
        dy = float(track_data["dy"])
        norm = math.hypot(dx, dy)
        if norm <= 1e-9:
            return None
        ux = dx / norm
        uy = dy / norm
        span_x = float(graph.space.x_range[1]) - float(graph.space.x_range[0])
        span_y = float(graph.space.y_range[1]) - float(graph.space.y_range[0])
        line_len = max(10.0, 2.0 * max(abs(span_x), abs(span_y)))
        half = 0.5 * line_len
        return (x0 - ux * half, y0 - uy * half, x0 + ux * half, y0 + uy * half)

    return None


def _motion_tau_bounds(motion: GraphMotion, *, default_key: str = "tau") -> tuple[str, float, float] | None:
    bounds = timeline_bounds(motion.timeline)
    if bounds is None:
        return None
    start_t, end_t = bounds
    args = dict(motion.args or {})
    param_key = str(args.get("param_key", default_key)).strip() or default_key
    tau_start = float(evaluate_timeline(motion.timeline, float(start_t), key=param_key))
    tau_end = float(evaluate_timeline(motion.timeline, float(end_t), key=param_key))
    if tau_end < tau_start:
        tau_start, tau_end = tau_end, tau_start
    return param_key, tau_start, tau_end


def precompute_physics_world(
    *,
    motion: GraphMotion,
    graph: CompositeGraph,
    base_poses: dict[str, Pose],
    geometries: dict[str, PartGeometry],
) -> PhysicsWorldResult | None:
    if str(motion.type).strip() != "physics_world":
        return None

    try:
        import pymunk  # type: ignore
    except Exception as exc:  # noqa: BLE001
        raise PhysicsWorldNotAvailable(
            "Motion type 'physics_world' requires pymunk. Install with: pip install pymunk"
        ) from exc

    tau_bounds = _motion_tau_bounds(motion)
    if tau_bounds is None:
        return None
    param_key, tau_start, tau_end = tau_bounds
    duration = float(tau_end - tau_start)
    if duration <= 1e-9:
        return PhysicsWorldResult(
            motion_id=str(motion.id),
            param_key=param_key,
            tau_start=float(tau_start),
            tau_end=float(tau_end),
            samples_by_part={},
            collision_events=[],
        )

    args = dict(motion.args or {})
    fps = _to_float(args.get("fps"), 120.0)
    if fps <= 1e-6:
        fps = 120.0
    substeps = max(1, _to_int(args.get("substeps"), 2))
    gravity_x, gravity_y = _parse_gravity(args.get("gravity"))
    allow_rotation_default = _to_bool(args.get("allow_rotation"), False)
    default_body_friction = max(0.0, _to_float(args.get("body_friction"), 0.0))
    default_body_elasticity = max(0.0, _to_float(args.get("body_elasticity"), 0.0))
    default_static_friction = max(0.0, _to_float(args.get("static_friction"), 0.0))
    default_static_elasticity = max(0.0, _to_float(args.get("static_elasticity"), 0.0))
    segment_radius = max(0.0, _to_float(args.get("track_radius"), 0.02))

    space = pymunk.Space()
    space.gravity = (float(gravity_x), float(gravity_y))

    part_type_by_id = {part.id: str(part.type).strip() for part in graph.parts}
    track_by_id = {track.id: (str(track.type).strip().lower(), dict(track.data or {})) for track in graph.tracks}

    static_tracks = args.get("static_tracks")
    track_ids: list[str] = []
    if isinstance(static_tracks, list):
        for item in static_tracks:
            if isinstance(item, str) and item.strip():
                track_ids.append(item.strip())
    if not track_ids:
        track_ids = [track_id for track_id, (track_type, _) in track_by_id.items() if track_type in {"line", "segment"}]
    track_ids = list(dict.fromkeys(track_ids))

    shape_owner: dict[int, str] = {}

    for track_id in track_ids:
        item = track_by_id.get(track_id)
        if item is None:
            continue
        track_type, track_data = item
        world_data = _track_data_to_world(
            track_type=track_type,
            track_data=track_data,
            poses=base_poses,
            geoms=geometries,
        )
        segment = _segment_from_track(track_type=track_type, track_data=world_data, graph=graph)
        if segment is None:
            continue
        shape = pymunk.Segment(
            space.static_body,
            (float(segment[0]), float(segment[1])),
            (float(segment[2]), float(segment[3])),
            float(segment_radius),
        )
        shape.friction = float(default_static_friction)
        shape.elasticity = float(default_static_elasticity)
        space.add(shape)
        shape_owner[id(shape)] = f"track:{track_id}"

    bodies_raw = args.get("bodies")
    if not isinstance(bodies_raw, list):
        return None

    body_by_part: dict[str, Any] = {}
    allow_rotation_by_part: dict[str, bool] = {}
    dynamic_collision_type_base = 1000

    for index, item in enumerate(bodies_raw):
        if not isinstance(item, dict):
            continue
        part_id_raw = item.get("part_id")
        if not isinstance(part_id_raw, str) or not part_id_raw.strip():
            continue
        part_id = part_id_raw.strip()
        if part_id in body_by_part:
            continue
        pose = base_poses.get(part_id)
        geom = geometries.get(part_id)
        if pose is None or geom is None:
            continue

        part_type = part_type_by_id.get(part_id, "")
        shape_mode = str(item.get("shape", "auto")).strip().lower()
        if shape_mode == "auto":
            shape_mode = "box" if part_type in {"Block", "Cart", "Weight", "SemicircleCart", "QuarterCart"} else "circle"
        if shape_mode not in {"box", "circle"}:
            shape_mode = "box"

        width, height = _geometry_size(geom)
        scale = max(1e-6, float(pose.scale))
        width *= scale
        height *= scale

        mass = _to_float(item.get("mass"), 1.0)
        if mass <= 1e-9:
            mass = 1.0
        allow_rotation = _to_bool(item.get("allow_rotation"), allow_rotation_default)

        if shape_mode == "circle":
            radius = _to_float(item.get("radius"), 0.5 * min(width, height))
            if radius <= 1e-6:
                radius = 0.2
            if allow_rotation:
                moment = _to_float(item.get("moment"), float(pymunk.moment_for_circle(float(mass), 0.0, float(radius))))
            else:
                moment = float("inf")
            body = pymunk.Body(float(mass), float(moment))
            shape = pymunk.Circle(body, float(radius))
        else:
            box_size = (max(1e-6, float(width)), max(1e-6, float(height)))
            if allow_rotation:
                moment = _to_float(item.get("moment"), float(pymunk.moment_for_box(float(mass), box_size)))
            else:
                moment = float("inf")
            body = pymunk.Body(float(mass), float(moment))
            shape = pymunk.Poly.create_box(body, box_size)

        body.position = (float(pose.x), float(pose.y))
        body.velocity = (_to_float(item.get("vx0"), 0.0), _to_float(item.get("vy0"), 0.0))
        body.angle = math.radians(float(pose.theta))
        body.angular_velocity = _to_float(item.get("omega0"), 0.0)
        if not allow_rotation:
            body.angular_velocity = 0.0

        shape.friction = max(0.0, _to_float(item.get("friction"), default_body_friction))
        shape.elasticity = max(0.0, _to_float(item.get("elasticity"), default_body_elasticity))
        shape.collision_type = dynamic_collision_type_base + int(index)

        space.add(body, shape)
        body_by_part[part_id] = body
        allow_rotation_by_part[part_id] = bool(allow_rotation)
        shape_owner[id(shape)] = part_id

    if not body_by_part:
        return None

    collision_events: list[dict[str, Any]] = []
    sim_state = {"tau": float(tau_start)}

    def _post_solve(arbiter, _space, _data) -> None:  # pragma: no cover - callback behavior is exercised in integration rendering
        try:
            if not bool(getattr(arbiter, "is_first_contact", False)):
                return
            s_a, s_b = arbiter.shapes
            owner_a = shape_owner.get(id(s_a), "")
            owner_b = shape_owner.get(id(s_b), "")
            if not owner_a or not owner_b:
                return
            impulse = getattr(arbiter, "total_impulse", None)
            normal = getattr(arbiter, "normal", None)
            impulse_mag = 0.0
            if impulse is not None and hasattr(impulse, "length"):
                impulse_mag = float(impulse.length)
            normal_x = float(normal.x) if normal is not None and hasattr(normal, "x") else 0.0
            normal_y = float(normal.y) if normal is not None and hasattr(normal, "y") else 0.0
            collision_events.append(
                {
                    "tau": float(sim_state["tau"]),
                    "a": owner_a,
                    "b": owner_b,
                    "impulse": float(impulse_mag),
                    "normal": [normal_x, normal_y],
                }
            )
        except Exception:
            return

    space.on_collision(None, None, post_solve=_post_solve)

    dt = 1.0 / float(fps)
    step_dt = dt / float(substeps)
    frame_count = int(duration * fps) + 1
    tau_sign = 1.0 if tau_end >= tau_start else -1.0

    samples_by_part: dict[str, list[dict[str, float]]] = {part_id: [] for part_id in body_by_part}

    tau_value = float(tau_start)
    for _ in range(frame_count):
        for part_id, body in body_by_part.items():
            theta = math.degrees(float(body.angle)) if allow_rotation_by_part.get(part_id, False) else float(base_poses[part_id].theta)
            samples_by_part[part_id].append(
                {
                    "tau": float(tau_value),
                    "x": float(body.position.x),
                    "y": float(body.position.y),
                    "theta": float(theta),
                }
            )
        for _sub in range(substeps):
            sim_state["tau"] = float(tau_value)
            space.step(float(step_dt))
            tau_value += tau_sign * float(step_dt)

    return PhysicsWorldResult(
        motion_id=str(motion.id),
        param_key=param_key,
        tau_start=float(tau_start),
        tau_end=float(tau_end),
        samples_by_part=samples_by_part,
        collision_events=collision_events,
    )


def _interp_value(t0: float, v0: float, t1: float, v1: float, t: float) -> float:
    if abs(t1 - t0) <= 1e-9:
        return float(v1)
    alpha = (float(t) - float(t0)) / (float(t1) - float(t0))
    if alpha < 0.0:
        alpha = 0.0
    if alpha > 1.0:
        alpha = 1.0
    return float(v0 + (v1 - v0) * alpha)


def sample_physics_world(result: PhysicsWorldResult, *, tau_value: float) -> dict[str, Pose]:
    sampled: dict[str, Pose] = {}
    tau = float(tau_value)
    for part_id, series in result.samples_by_part.items():
        if not series:
            continue
        if tau <= float(series[0]["tau"]):
            item = series[0]
            sampled[part_id] = Pose(x=float(item["x"]), y=float(item["y"]), theta=float(item["theta"]), scale=1.0, z=0.0)
            continue
        if tau >= float(series[-1]["tau"]):
            item = series[-1]
            sampled[part_id] = Pose(x=float(item["x"]), y=float(item["y"]), theta=float(item["theta"]), scale=1.0, z=0.0)
            continue

        for index in range(1, len(series)):
            left = series[index - 1]
            right = series[index]
            t0 = float(left["tau"])
            t1 = float(right["tau"])
            if t0 <= tau <= t1:
                x = _interp_value(t0, float(left["x"]), t1, float(right["x"]), tau)
                y = _interp_value(t0, float(left["y"]), t1, float(right["y"]), tau)
                theta = _interp_value(t0, float(left["theta"]), t1, float(right["theta"]), tau)
                sampled[part_id] = Pose(x=float(x), y=float(y), theta=float(theta), scale=1.0, z=0.0)
                break
    return sampled
