from __future__ import annotations

from manim import DEGREES, ORIGIN, VGroup

from components.base import Component, ComponentDefaults
from components.common.bullet_panel import BulletPanel
from components.common.formula import Formula
from components.common.text_block import TextBlock
from components.physics.object_components import build_physics_components
from render.composite.anchors import geometry_from_mobject
from render.composite.motion import resolve_motion_pose_args
from render.composite.track_baker import bake_local_tracks_to_world
from render.composite.solver import SolveOptions, solve_static
from render.composite.types import Pose
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

        graph_for_bake = _without_on_track_pose_constraints(graph)
        bake_result = solve_static(graph_for_bake, geometries=geometries, options=solve_options)
        baked_track_poses = bake_result.poses
        if bake_result.unsatisfied_hard():
            baked_track_poses = self._seed_poses(graph)
        runtime_graph = bake_local_tracks_to_world(graph, poses=baked_track_poses, geometries=geometries)

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

            for part_id in part_order:
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

        _render_at(runtime["time"])
        return group
