from __future__ import annotations

import math
from typing import Any

from manim import DEGREES, ORIGIN, VGroup

from components.base import Component, ComponentDefaults
from components.common.bullet_panel import BulletPanel
from components.common.formula import Formula
from components.common.text_block import TextBlock
from components.physics.object_components import build_physics_components
from render.composite.anchors import geometry_from_mobject
from render.composite.motion import (
    evaluate_state_driver_target,
    evaluate_timeline,
    find_state_driver_end_event,
    resolve_motion_pose_args,
    timeline_bounds,
)
from render.composite.physics_world import (
    PhysicsWorldNotAvailable,
    precompute_physics_world,
    sample_physics_world,
)
from render.composite.solver.on_track_pose import apply as apply_on_track_pose
from render.composite.track_baker import bake_local_tracks_to_world
from render.composite.solver import SolveOptions, solve_static
from render.composite.types import Pose, anchor_world
from schema.composite_graph_models import CompositeGraph, GraphConstraint, GraphPart
from schema.scene_plan_models import ObjectSpec


def _clone_poses(poses: dict[str, Pose]) -> dict[str, Pose]:
    return {part_id: pose.copy() for part_id, pose in poses.items()}


def _apply_motion_pose_constraints(graph: CompositeGraph, *, time_value: float) -> CompositeGraph:
    if not graph.motions:
        return graph

    solve_graph = graph.model_copy(deep=True)
    pose_args_list = resolve_motion_pose_args(graph, time_value=time_value)
    if not pose_args_list:
        return solve_graph

    existing_by_part: dict[str, int] = {}
    for index, constraint in enumerate(solve_graph.constraints):
        if constraint.type != "on_track_pose":
            continue
        part_id = str(constraint.args.get("part_id", "")).strip()
        if part_id and part_id not in existing_by_part:
            existing_by_part[part_id] = index

    existing_ids = {constraint.id for constraint in solve_graph.constraints}
    for pose_args in pose_args_list:
        part_id = str(pose_args.get("part_id", "")).strip()
        if not part_id:
            continue

        index = existing_by_part.get(part_id)
        if index is not None:
            merged = dict(solve_graph.constraints[index].args or {})
            merged.update(pose_args)
            solve_graph.constraints[index].args = merged
            continue

        constraint_id = f"__motion_pose_{part_id}"
        suffix = 2
        while constraint_id in existing_ids:
            constraint_id = f"__motion_pose_{part_id}_{suffix}"
            suffix += 1
        solve_graph.constraints.append(
            GraphConstraint(
                id=constraint_id,
                type="on_track_pose",
                args=dict(pose_args),
                hard=True,
            )
        )
        existing_ids.add(constraint_id)

    return solve_graph


def _without_on_track_pose_constraints(graph: CompositeGraph) -> CompositeGraph:
    filtered = [constraint.model_copy(deep=True) for constraint in graph.constraints if constraint.type != "on_track_pose"]
    if len(filtered) == len(graph.constraints):
        return graph
    return graph.model_copy(update={"constraints": filtered})


def _to_bool(value: object, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False
    return default


def _to_float(value: object, default: float) -> float:
    try:
        return float(value)
    except Exception:  # noqa: BLE001
        return float(default)


def _track_data_to_world(
    *,
    track_type: str,
    track_data: dict,
    poses: dict[str, Pose],
    geoms: dict[str, object],
) -> dict:
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


def _project_point_to_track_s(
    *,
    track_type: str,
    track_data: dict,
    point: tuple[float, float],
) -> float | None:
    px, py = float(point[0]), float(point[1])
    if track_type in {"line", "segment"} and {"x1", "y1", "x2", "y2"}.issubset(track_data):
        x1 = float(track_data.get("x1", 0.0))
        y1 = float(track_data.get("y1", 0.0))
        x2 = float(track_data.get("x2", x1))
        y2 = float(track_data.get("y2", y1))
        dx = x2 - x1
        dy = y2 - y1
        denom = dx * dx + dy * dy
        if denom <= 1e-12:
            return 0.0
        s = ((px - x1) * dx + (py - y1) * dy) / denom
        if track_type == "segment":
            if s < 0.0:
                s = 0.0
            if s > 1.0:
                s = 1.0
        return float(s)
    if track_type == "line" and {"x0", "y0", "dx", "dy"}.issubset(track_data):
        x0 = float(track_data.get("x0", 0.0))
        y0 = float(track_data.get("y0", 0.0))
        dx = float(track_data.get("dx", 1.0))
        dy = float(track_data.get("dy", 0.0))
        denom = dx * dx + dy * dy
        if denom <= 1e-12:
            return 0.0
        return float(((px - x0) * dx + (py - y0) * dy) / denom)
    return None


def _is_local_anchor_ref_line_segment(track) -> bool:
    ttype = str(track.type).strip().lower()
    if ttype not in {"line", "segment"}:
        return False
    data = dict(track.data or {})
    if str(data.get("space", "local")).strip().lower() == "world":
        return False
    part_id = str(data.get("part_id", "")).strip()
    anchor_a = str(data.get("anchor_a") or data.get("a1") or "").strip()
    anchor_b = str(data.get("anchor_b") or data.get("a2") or "").strip()
    return bool(part_id and anchor_a and anchor_b)


def _collect_referenced_track_ids(graph: CompositeGraph) -> set[str]:
    refs: set[str] = set()
    for constraint in graph.constraints:
        if constraint.type != "on_track_pose":
            continue
        track_id = constraint.args.get("track_id")
        if isinstance(track_id, str) and track_id.strip():
            refs.add(track_id.strip())

    for motion in graph.motions:
        args = dict(motion.args or {})
        if motion.type == "on_track":
            track_id = args.get("track_id")
            if isinstance(track_id, str) and track_id.strip():
                refs.add(track_id.strip())
            continue
        if motion.type != "on_track_schedule":
            continue
        segments = args.get("segments")
        if not isinstance(segments, list):
            continue
        for segment in segments:
            if not isinstance(segment, dict):
                continue
            track_id = segment.get("track_id")
            if isinstance(track_id, str) and track_id.strip():
                refs.add(track_id.strip())
    return refs


def _resolve_preserve_line_segment_track_ids(graph: CompositeGraph, *, mode: str) -> set[str]:
    candidates = {track.id for track in graph.tracks if _is_local_anchor_ref_line_segment(track)}
    if mode == "baked":
        return set()
    if mode == "follow_part":
        return candidates
    # auto: preserve only tracks actually used by pose constraints or motions.
    return candidates & _collect_referenced_track_ids(graph)


def _state_driver_motions(graph: CompositeGraph) -> list:
    return [motion for motion in graph.motions if str(motion.type).strip() == "state_driver"]


def _normalize_anchor_name(value: Any, default: str = "center") -> str:
    if isinstance(value, str) and value.strip():
        return value.strip().lower()
    return default


def _collect_stretch_spring_links(
    graph: CompositeGraph,
    *,
    part_type_by_id: dict[str, str],
) -> dict[str, dict[str, tuple[str, str]]]:
    links: dict[str, dict[str, tuple[str, str]]] = {}

    for constraint in graph.constraints:
        if str(constraint.type).strip() != "attach":
            continue
        args = dict(constraint.args or {})

        part_a = str(args.get("part_a", "")).strip()
        part_b = str(args.get("part_b", "")).strip()
        if not part_a or not part_b:
            continue

        anchor_a = _normalize_anchor_name(args.get("anchor_a", args.get("from_anchor", args.get("anchor"))))
        anchor_b = _normalize_anchor_name(args.get("anchor_b", args.get("to_anchor")))

        if part_type_by_id.get(part_a) == "Spring" and anchor_a in {"start", "end"} and part_a != part_b:
            links.setdefault(part_a, {})[anchor_a] = (part_b, anchor_b)
        if part_type_by_id.get(part_b) == "Spring" and anchor_b in {"start", "end"} and part_a != part_b:
            links.setdefault(part_b, {})[anchor_b] = (part_a, anchor_a)

    return {spring_id: endpoint_map for spring_id, endpoint_map in links.items() if {"start", "end"}.issubset(endpoint_map)}


def _collect_stretch_spring_constraint_ids(
    graph: CompositeGraph,
    *,
    part_type_by_id: dict[str, str],
) -> set[str]:
    constraint_ids: set[str] = set()
    for constraint in graph.constraints:
        if str(constraint.type).strip() != "attach":
            continue
        args = dict(constraint.args or {})
        part_a = str(args.get("part_a", "")).strip()
        part_b = str(args.get("part_b", "")).strip()
        anchor_a = _normalize_anchor_name(args.get("anchor_a", args.get("from_anchor", args.get("anchor"))))
        anchor_b = _normalize_anchor_name(args.get("anchor_b", args.get("to_anchor")))
        if part_type_by_id.get(part_a) == "Spring" and anchor_a in {"start", "end"} and part_b:
            constraint_ids.add(str(constraint.id))
            continue
        if part_type_by_id.get(part_b) == "Spring" and anchor_b in {"start", "end"} and part_a:
            constraint_ids.add(str(constraint.id))
    return constraint_ids


class CompositeObjectComponent(Component):
    type_name = "CompositeObject"

    def __init__(self):
        # Reuse the existing component library for inner parts.
        self._part_components = {
            TextBlock.type_name: TextBlock(),
            BulletPanel.type_name: BulletPanel(),
            Formula.type_name: Formula(),
            **build_physics_components(),
        }

    def _build_part_spec(self, part: GraphPart) -> ObjectSpec:
        return ObjectSpec(
            type=part.type,
            params=dict(part.params),
            style=dict(part.style),
            priority=2,
        )

    def _build_base_part(self, part: GraphPart, *, defaults: ComponentDefaults):
        if part.type == self.type_name:
            raise ValueError("CompositeObject cannot recursively contain CompositeObject parts")

        component = self._part_components.get(part.type)
        if component is None:
            raise KeyError(f"Unknown CompositeObject part type: {part.type}")

        mobj = component.build(self._build_part_spec(part), defaults=defaults)
        mobj.move_to([0.0, 0.0, 0.0])
        return mobj

    def _seed_poses(self, graph: CompositeGraph) -> dict[str, Pose]:
        return {
            part.id: Pose(
                x=float(part.seed_pose.x),
                y=float(part.seed_pose.y),
                theta=float(part.seed_pose.theta),
                scale=float(part.seed_pose.scale),
                z=float(part.seed_pose.z),
            )
            for part in graph.parts
        }

    def _apply_pose(self, mobj, pose: Pose) -> None:
        if pose.scale != 1.0:
            mobj.scale(float(pose.scale), about_point=mobj.get_center())
        if pose.theta != 0.0:
            mobj.rotate(float(pose.theta) * DEGREES, about_point=mobj.get_center())
        mobj.move_to([float(pose.x), float(pose.y), float(pose.z)])

    def build(self, spec: ObjectSpec, *, defaults: ComponentDefaults):
        graph_raw = spec.params.get("graph")
        if graph_raw is None:
            raise ValueError("CompositeObject requires params.graph")
        graph = CompositeGraph.model_validate(graph_raw)

        template_parts: dict[str, object] = {}
        geometries = {}
        for part in graph.parts:
            template = self._build_base_part(part, defaults=defaults)
            template_parts[part.id] = template
            geometries[part.id] = geometry_from_mobject(part.id, template)

        solve_options = SolveOptions(
            max_iters=int(spec.params.get("solver_max_iters", 80)),
            tolerance=float(spec.params.get("solver_tolerance", 1e-3)),
        )

        track_bind_mode_raw = spec.params.get("track_bind_mode", "auto")
        track_bind_mode = str(track_bind_mode_raw).strip().lower() if track_bind_mode_raw is not None else "auto"
        if track_bind_mode not in {"auto", "baked", "follow_part"}:
            track_bind_mode = "auto"
        preserve_track_ids = _resolve_preserve_line_segment_track_ids(graph, mode=track_bind_mode)

        graph_for_bake = _without_on_track_pose_constraints(graph)
        bake_result = solve_static(graph_for_bake, geometries=geometries, options=solve_options)
        baked_track_poses = bake_result.poses
        if bake_result.unsatisfied_hard():
            baked_track_poses = self._seed_poses(graph)
        runtime_graph = bake_local_tracks_to_world(
            graph,
            poses=baked_track_poses,
            geometries=geometries,
            preserve_line_segment_track_ids=preserve_track_ids,
        )
        part_type_by_id = {part.id: str(part.type) for part in runtime_graph.parts}
        stretch_spring_links = _collect_stretch_spring_links(
            runtime_graph,
            part_type_by_id=part_type_by_id,
        )
        if stretch_spring_links:
            ignore_constraint_ids = _collect_stretch_spring_constraint_ids(
                runtime_graph,
                part_type_by_id=part_type_by_id,
            )
            if ignore_constraint_ids:
                runtime_graph = runtime_graph.model_copy(
                    update={
                        "constraints": [
                            constraint.model_copy(deep=True)
                            for constraint in runtime_graph.constraints
                            if str(constraint.id) not in ignore_constraint_ids
                        ]
                    },
                    deep=True,
                )

        solve_result = solve_static(runtime_graph, geometries=geometries, options=solve_options)
        base_poses = solve_result.poses
        if solve_result.unsatisfied_hard():
            # Conservative fallback: render seed pose when hard constraints cannot be satisfied.
            base_poses = self._seed_poses(runtime_graph)

        part_order = [part.id for part in graph.parts]
        rendered_parts = {part_id: template_parts[part_id].copy() for part_id in part_order}
        group = VGroup(*[rendered_parts[part_id] for part_id in part_order])

        runtime = {
            "scale": 1.0,
            "tx": 0.0,
            "ty": 0.0,
            "time": float(spec.params.get("motion_time", 0.0)),
            "last_good_poses": _clone_poses(base_poses),
        }
        state_driver_motions = _state_driver_motions(runtime_graph)
        physics_world_entries: list[tuple[Any, Any]] = []
        physics_world_warnings: list[str] = []
        for motion in runtime_graph.motions:
            if str(motion.type).strip() != "physics_world":
                continue
            try:
                result = precompute_physics_world(
                    motion=motion,
                    graph=runtime_graph,
                    base_poses=base_poses,
                    geometries=geometries,
                )
            except PhysicsWorldNotAvailable as exc:
                physics_world_warnings.append(str(exc))
                continue
            except Exception as exc:  # noqa: BLE001
                physics_world_warnings.append(f"physics_world motion '{motion.id}' failed: {exc}")
                continue
            if result is not None:
                physics_world_entries.append((motion, result))

        motion_by_id = {str(motion.id): motion for motion in runtime_graph.motions}
        motion_graph_by_id = {
            str(motion.id): runtime_graph.model_copy(update={"motions": [motion]}, deep=True)
            for motion in runtime_graph.motions
        }
        tracks_for_motion = {track.id: (track.type, dict(track.data or {})) for track in runtime_graph.tracks}
        track_motion_pose_cache: dict[float, dict[str, Pose]] = {}
        state_driver_handoff_cache: dict[str, dict[str, float]] = {}
        state_driver_end_cache: dict[tuple[str, tuple[tuple[str, float], ...]], dict[str, Any] | None] = {}

        def _world_anchor_of_part(part_id: str, anchor_name: str, *, poses: dict[str, Pose]) -> tuple[float, float] | None:
            pose = poses.get(part_id)
            geom = geometries.get(part_id)
            if pose is None or geom is None:
                return None
            try:
                local = geom.anchor_local(anchor_name)
            except Exception:  # noqa: BLE001
                return None
            return anchor_world(pose, local)

        def _render_stretched_spring(part_id: str, *, poses: dict[str, Pose]):
            endpoint_map = stretch_spring_links.get(part_id)
            if not endpoint_map:
                return None

            start_ref = endpoint_map.get("start")
            end_ref = endpoint_map.get("end")
            if start_ref is None or end_ref is None:
                return None

            start_world = _world_anchor_of_part(start_ref[0], start_ref[1], poses=poses)
            end_world = _world_anchor_of_part(end_ref[0], end_ref[1], poses=poses)
            if start_world is None or end_world is None:
                return None

            dx = float(end_world[0] - start_world[0])
            dy = float(end_world[1] - start_world[1])
            distance = math.hypot(dx, dy)
            if distance <= 1e-6:
                return None

            spring = template_parts[part_id].copy()
            base_len = 0.0
            get_anchor = getattr(spring, "get_anchor", None)
            if callable(get_anchor):
                try:
                    start_anchor = get_anchor("start")
                    end_anchor = get_anchor("end")
                    base_len = math.hypot(
                        float(end_anchor[0]) - float(start_anchor[0]),
                        float(end_anchor[1]) - float(start_anchor[1]),
                    )
                except Exception:  # noqa: BLE001
                    base_len = 0.0
            if base_len <= 1e-6:
                base_len = max(float(getattr(spring, "width", 0.0)), 1e-6)

            stretch_factor = float(distance / base_len)
            spring.stretch(stretch_factor, dim=0, about_point=spring.get_center())

            angle = math.atan2(dy, dx)
            spring.rotate(angle, about_point=spring.get_center())
            spring.move_to(
                [
                    0.5 * (float(start_world[0]) + float(end_world[0])),
                    0.5 * (float(start_world[1]) + float(end_world[1])),
                    0.0,
                ]
            )
            return spring

        def _solve_track_pose_at(time_point: float) -> dict[str, Pose]:
            cache_key = round(float(time_point), 6)
            cached = track_motion_pose_cache.get(cache_key)
            if cached is not None:
                return _clone_poses(cached)

            solve_graph_at = _apply_motion_pose_constraints(runtime_graph, time_value=float(time_point))
            solve_result_at = solve_static(solve_graph_at, geometries=geometries, options=solve_options)
            poses_at = solve_result_at.poses
            if solve_result_at.unsatisfied_hard():
                poses_at = _clone_poses(base_poses)

            track_motion_pose_cache[cache_key] = _clone_poses(poses_at)
            return _clone_poses(poses_at)

        def _resolve_state_driver_handoff(motion) -> dict[str, float]:
            motion_id = str(motion.id)
            cached = state_driver_handoff_cache.get(motion_id)
            if cached is not None:
                return dict(cached)

            args = dict(motion.args or {})
            handoff_raw = args.get("handoff")
            if not isinstance(handoff_raw, dict):
                state_driver_handoff_cache[motion_id] = {}
                return {}

            part_id = str(args.get("part_id", "")).strip()
            if not part_id:
                state_driver_handoff_cache[motion_id] = {}
                return {}

            bounds = timeline_bounds(motion.timeline)
            if bounds is None:
                state_driver_handoff_cache[motion_id] = {}
                return {}

            from_time = _to_float(handoff_raw.get("from_time"), float(bounds[0]))
            result: dict[str, float] = {}
            use_position = _to_bool(handoff_raw.get("position"), True)
            use_velocity = _to_bool(handoff_raw.get("velocity"), False)

            if use_position:
                poses_at = _solve_track_pose_at(from_time)
                pose = poses_at.get(part_id)
                if pose is not None:
                    result["x0"] = float(pose.x)
                    result["y0"] = float(pose.y)

            if use_velocity:
                dt = abs(_to_float(handoff_raw.get("dt"), 1e-3))
                if dt <= 1e-6:
                    dt = 1e-3
                t0 = max(0.0, float(from_time) - float(dt))
                t1 = float(from_time) + float(dt)
                if t1 <= t0 + 1e-9:
                    t1 = t0 + 1e-3
                poses_0 = _solve_track_pose_at(t0)
                poses_1 = _solve_track_pose_at(t1)
                pose_0 = poses_0.get(part_id)
                pose_1 = poses_1.get(part_id)
                if pose_0 is not None and pose_1 is not None:
                    inv_dt = 1.0 / (t1 - t0)
                    result["vx0"] = float(pose_1.x - pose_0.x) * inv_dt
                    result["vy0"] = float(pose_1.y - pose_0.y) * inv_dt

            state_driver_handoff_cache[motion_id] = dict(result)
            return result

        def _handoff_state_cache_key(handoff_state: dict[str, float]) -> tuple[tuple[str, float], ...]:
            pairs: list[tuple[str, float]] = []
            for key, value in sorted(handoff_state.items()):
                if isinstance(value, (int, float)):
                    pairs.append((str(key), round(float(value), 8)))
            return tuple(pairs)

        def _resolve_state_driver_end(motion, *, handoff_state: dict[str, float]) -> dict[str, Any] | None:
            motion_id = str(motion.id)
            cache_key = (motion_id, _handoff_state_cache_key(handoff_state))
            if cache_key in state_driver_end_cache:
                cached = state_driver_end_cache[cache_key]
                return None if cached is None else dict(cached)

            event = find_state_driver_end_event(
                motion,
                handoff_state=handoff_state,
            )
            state_driver_end_cache[cache_key] = None if event is None else dict(event)
            return None if event is None else dict(event)

        def _apply_shifted_handoff_motion(
            *,
            handoff_motion_id: str,
            now_time: float,
            event_time: float,
            poses: dict[str, Pose],
            event_target: dict[str, float] | None = None,
        ) -> bool:
            motion = motion_by_id.get(handoff_motion_id)
            if motion is None:
                return False
            motion_type = str(motion.type).strip()
            if motion_type not in {"on_track", "on_track_schedule"}:
                return False

            bounds = timeline_bounds(motion.timeline)
            if bounds is None:
                return False
            start_t, _ = bounds
            elapsed = float(now_time) - float(event_time)
            shifted_time = float(start_t) + elapsed
            motion_args = dict(motion.args or {})
            part_id = str(motion_args.get("part_id", "")).strip()
            if motion_type == "on_track":
                track_id = str(motion_args.get("track_id", "")).strip()
                if not track_id or track_id not in tracks_for_motion or not part_id or part_id not in poses:
                    return False
                track_type, track_data = tracks_for_motion[track_id]
                world_track_data = _track_data_to_world(
                    track_type=str(track_type).strip().lower(),
                    track_data=track_data,
                    poses=poses,
                    geoms=geometries,
                )

                if isinstance(event_target, dict):
                    try:
                        vx = float(event_target.get("vx")) if event_target.get("vx") is not None else None
                        vy = float(event_target.get("vy")) if event_target.get("vy") is not None else None
                    except Exception:  # noqa: BLE001
                        vx, vy = None, None
                    if vx is not None and vy is not None:
                        length_scale = 0.0
                        tan_x, tan_y = 1.0, 0.0
                        if {"x1", "y1", "x2", "y2"}.issubset(world_track_data):
                            dx = float(world_track_data.get("x2", 0.0)) - float(world_track_data.get("x1", 0.0))
                            dy = float(world_track_data.get("y2", 0.0)) - float(world_track_data.get("y1", 0.0))
                            length_scale = (dx * dx + dy * dy) ** 0.5
                            if length_scale > 1e-9:
                                tan_x, tan_y = dx / length_scale, dy / length_scale
                        elif {"dx", "dy"}.issubset(world_track_data):
                            dx = float(world_track_data.get("dx", 1.0))
                            dy = float(world_track_data.get("dy", 0.0))
                            length_scale = (dx * dx + dy * dy) ** 0.5
                            if length_scale > 1e-9:
                                tan_x, tan_y = dx / length_scale, dy / length_scale
                        if length_scale > 1e-9:
                            param_key = str(motion_args.get("param_key", "s")).strip() or "s"
                            ds0 = _to_float(evaluate_timeline(motion.timeline, float(start_t), key=param_key), 0.0)
                            ds1 = _to_float(evaluate_timeline(motion.timeline, float(start_t) + 1e-3, key=param_key), ds0)
                            base_ds_dt = (ds1 - ds0) / 1e-3
                            target_ds_dt = (vx * tan_x + vy * tan_y) / length_scale
                            if abs(base_ds_dt) > 1e-9 and target_ds_dt * base_ds_dt > 0:
                                time_scale = target_ds_dt / base_ds_dt
                                if 0.1 <= abs(time_scale) <= 10.0:
                                    shifted_time = float(start_t) + elapsed * time_scale

                param_key = str(motion_args.get("param_key", "s")).strip() or "s"
                s_now = _to_float(evaluate_timeline(motion.timeline, shifted_time, key=param_key), 0.0)
                s_start = _to_float(evaluate_timeline(motion.timeline, float(start_t), key=param_key), 0.0)
                s_offset = 0.0
                if isinstance(event_target, dict):
                    try:
                        part_geom = geometries.get(part_id)
                        if part_geom is not None:
                            anchor_name = str(motion_args.get("anchor", "bottom_center") or "bottom_center")
                            local_anchor = part_geom.anchor_local(anchor_name)
                            current_pose = poses[part_id]
                            pose_at_event = Pose(
                                x=float(event_target.get("x", current_pose.x)),
                                y=float(event_target.get("y", current_pose.y)),
                                theta=float(event_target.get("theta", current_pose.theta)),
                                scale=float(current_pose.scale),
                                z=float(current_pose.z),
                            )
                            anchor_point = anchor_world(pose_at_event, local_anchor)
                            s_hit = _project_point_to_track_s(
                                track_type=str(track_type).strip().lower(),
                                track_data=world_track_data,
                                point=anchor_point,
                            )
                            if isinstance(s_hit, (int, float)):
                                s_offset = float(s_hit) - float(s_start)
                    except Exception:  # noqa: BLE001
                        s_offset = 0.0

                pose_args = dict(motion_args)
                pose_args["part_id"] = part_id
                pose_args["track_id"] = track_id
                pose_args["s"] = float(s_now) + float(s_offset)
                if "angle_mode" not in pose_args and ("theta_mode" in pose_args or "orient" in pose_args):
                    pose_args["angle_mode"] = str(
                        pose_args.get("theta_mode", pose_args.get("orient", "keep"))
                    )
                apply_on_track_pose(
                    args=pose_args,
                    poses=poses,
                    geoms=geometries,
                    tracks=tracks_for_motion,
                )
                return True

            motion_graph = motion_graph_by_id.get(handoff_motion_id)
            if motion_graph is None:
                return False

            pose_args_list = resolve_motion_pose_args(motion_graph, time_value=shifted_time)
            if not pose_args_list:
                return False
            for pose_args in pose_args_list:
                apply_on_track_pose(
                    args=pose_args,
                    poses=poses,
                    geoms=geometries,
                    tracks=tracks_for_motion,
                )
            return True

        def _render_at(time_value: float) -> None:
            runtime["time"] = float(time_value)
            poses = _clone_poses(base_poses)
            if runtime_graph.motions:
                solve_graph = _apply_motion_pose_constraints(runtime_graph, time_value=runtime["time"])
                solve_result_now = solve_static(solve_graph, geometries=geometries, options=solve_options)
                if solve_result_now.unsatisfied_hard():
                    poses = _clone_poses(runtime["last_good_poses"])
                else:
                    poses = solve_result_now.poses
                    runtime["last_good_poses"] = _clone_poses(poses)
                group.composite_residuals = solve_result_now.residuals  # type: ignore[attr-defined]

            if state_driver_motions:
                for motion in state_driver_motions:
                    args = dict(motion.args or {})
                    part_id = str(args.get("part_id", "")).strip()
                    if not part_id or part_id not in poses:
                        continue
                    handoff_state = _resolve_state_driver_handoff(motion)
                    end_event = _resolve_state_driver_end(motion, handoff_state=handoff_state)
                    active_time = float(runtime["time"])
                    if end_event is not None and float(runtime["time"]) > float(end_event.get("time", 0.0)) + 1e-9:
                        event_time = float(end_event["time"])
                        handoff_to = args.get("handoff_to")
                        handoff_applied = False
                        if isinstance(handoff_to, str) and handoff_to.strip():
                            handoff_applied = _apply_shifted_handoff_motion(
                                handoff_motion_id=handoff_to.strip(),
                                now_time=float(runtime["time"]),
                                event_time=event_time,
                                poses=poses,
                                event_target=end_event.get("target") if isinstance(end_event, dict) else None,
                            )
                        if handoff_applied:
                            continue
                        if _to_bool(args.get("hold_after"), True):
                            active_time = event_time
                        else:
                            continue

                    target = evaluate_state_driver_target(
                        motion,
                        time_value=active_time,
                        current_pose=poses.get(part_id),
                        handoff_state=handoff_state,
                    )
                    if target is None:
                        continue
                    pose = poses[part_id]
                    pose.x = float(target["x"])
                    pose.y = float(target["y"])
                    if "theta" in target:
                        pose.theta = float(target["theta"])

            if physics_world_entries:
                for motion, world_result in physics_world_entries:
                    tau_value = evaluate_timeline(
                        motion.timeline,
                        float(runtime["time"]),
                        key=str(world_result.param_key or "tau"),
                    )
                    sampled = sample_physics_world(world_result, tau_value=float(tau_value))
                    for part_id, sampled_pose in sampled.items():
                        if part_id not in poses:
                            continue
                        pose = poses[part_id]
                        pose.x = float(sampled_pose.x)
                        pose.y = float(sampled_pose.y)
                        pose.theta = float(sampled_pose.theta)

            runtime["last_good_poses"] = _clone_poses(poses)

            for part_id in part_order:
                mobj = _render_stretched_spring(part_id, poses=poses)
                if mobj is None:
                    mobj = template_parts[part_id].copy()
                    self._apply_pose(mobj, poses[part_id])
                if runtime["scale"] != 1.0:
                    mobj.scale(float(runtime["scale"]), about_point=ORIGIN)
                if runtime["tx"] != 0.0 or runtime["ty"] != 0.0:
                    mobj.shift([float(runtime["tx"]), float(runtime["ty"]), 0.0])
                rendered_parts[part_id].become(mobj)

            group.composite_time = runtime["time"]  # type: ignore[attr-defined]

        def _set_placement(scale: float, tx: float, ty: float) -> None:
            # Apply placement as a relative affine update on current world transform:
            # x' = scale * x + shift
            s = float(scale)
            runtime["scale"] *= s
            runtime["tx"] = runtime["tx"] * s + float(tx)
            runtime["ty"] = runtime["ty"] * s + float(ty)
            _render_at(runtime["time"])

        def _set_placement_absolute(scale: float, tx: float, ty: float) -> None:
            runtime["scale"] = float(scale)
            runtime["tx"] = float(tx)
            runtime["ty"] = float(ty)
            _render_at(runtime["time"])

        group.composite_set_time = _render_at  # type: ignore[attr-defined]
        group.composite_set_placement = _set_placement  # type: ignore[attr-defined]
        group.composite_set_placement_absolute = _set_placement_absolute  # type: ignore[attr-defined]
        group.composite_residuals = solve_result.residuals  # type: ignore[attr-defined]
        world_events: list[dict[str, Any]] = []
        for motion, world_result in physics_world_entries:
            for event in world_result.collision_events:
                item = dict(event)
                item["motion_id"] = str(motion.id)
                world_events.append(item)
        group.composite_collision_events = world_events  # type: ignore[attr-defined]
        group.physics_world_warnings = list(physics_world_warnings)  # type: ignore[attr-defined]

        _render_at(runtime["time"])
        return group
