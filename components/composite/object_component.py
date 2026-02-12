from __future__ import annotations

from manim import DEGREES, ORIGIN, VGroup

from components.base import Component, ComponentDefaults
from components.common.bullet_panel import BulletPanel
from components.common.formula import Formula
from components.common.text_block import TextBlock
from components.physics.object_components import build_physics_components
from render.composite.anchors import geometry_from_mobject
from render.composite.motion import apply_motions
from render.composite.solver import SolveOptions, solve_static
from render.composite.types import Pose
from schema.composite_graph_models import CompositeGraph, GraphPart
from schema.scene_plan_models import ObjectSpec


def _clone_poses(poses: dict[str, Pose]) -> dict[str, Pose]:
    return {part_id: pose.copy() for part_id, pose in poses.items()}


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
        solve_result = solve_static(graph, geometries=geometries, options=solve_options)
        base_poses = solve_result.poses
        if solve_result.unsatisfied_hard():
            # Conservative fallback: render seed pose when hard constraints cannot be satisfied.
            base_poses = self._seed_poses(graph)

        part_order = [part.id for part in graph.parts]
        rendered_parts = {part_id: template_parts[part_id].copy() for part_id in part_order}
        group = VGroup(*[rendered_parts[part_id] for part_id in part_order])

        runtime = {
            "scale": 1.0,
            "tx": 0.0,
            "ty": 0.0,
            "time": float(spec.params.get("motion_time", 0.0)),
        }

        def _render_at(time_value: float) -> None:
            runtime["time"] = float(time_value)
            poses = _clone_poses(base_poses)
            if graph.motions:
                poses = apply_motions(graph, poses=poses, geometries=geometries, time_value=runtime["time"])

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

        group.composite_set_time = _render_at  # type: ignore[attr-defined]
        group.composite_set_placement = _set_placement  # type: ignore[attr-defined]
        group.composite_residuals = solve_result.residuals  # type: ignore[attr-defined]

        _render_at(runtime["time"])
        return group
