from __future__ import annotations

import math

from manim import DEGREES, Scene, ValueTracker, linear

from components.base import ComponentDefaults
from components.physics.object_components import build_physics_components
from render.composite.anchors import geometry_from_mobject
from render.composite.solver import SolveOptions, solve_static
from render.composite.types import Pose
from schema.composite_graph_models import CompositeGraph
from schema.scene_plan_models import ObjectSpec


def _apply_pose(mobj, pose: Pose) -> None:
    if pose.scale != 1.0:
        mobj.scale(float(pose.scale), about_point=mobj.get_center())
    if pose.theta != 0.0:
        mobj.rotate(float(pose.theta) * DEGREES, about_point=mobj.get_center())
    mobj.move_to([float(pose.x), float(pose.y), float(pose.z)])


class CompositeAnchorConstraintSlide(Scene):
    """
    Demo: one slider moves along incline -> flat -> arc -> flat.
    The rail geometry is assembled by anchor-based constraints.
    """

    def construct(self):
        graph = CompositeGraph.model_validate(
            {
                "version": "0.1",
                "parts": [
                    {
                        "id": "p_incline",
                        "type": "Wall",
                        "params": {"length": 4.0, "angle": 30, "rise_to": "left"},
                        "seed_pose": {"x": -4.2, "y": -0.2, "theta": 0.0, "scale": 1.0},
                    },
                    {
                        "id": "p_flat_left",
                        "type": "Rod",
                        "params": {"length": 3.0, "thickness": 0.1},
                        "seed_pose": {"x": -1.0, "y": -1.2, "theta": 0.0, "scale": 1.0},
                    },
                    {
                        "id": "p_arc",
                        "type": "ArcTrack",
                        "params": {
                            "center": [0.0, 0.0, 0.0],
                            "radius": 1.5,
                            "start_angle": 180.0,
                            "end_angle": 360.0,
                            "stroke_width": 4.0,
                        },
                        "seed_pose": {"x": 2.0, "y": -1.2, "theta": 0.0, "scale": 1.0},
                    },
                    {
                        "id": "p_flat_right",
                        "type": "Rod",
                        "params": {"length": 3.0, "thickness": 0.1},
                        "seed_pose": {"x": 5.0, "y": -1.2, "theta": 0.0, "scale": 1.0},
                    },
                    {
                        "id": "p_slider",
                        "type": "Block",
                        "params": {"width": 0.9, "height": 0.55, "label": "P"},
                        "seed_pose": {"x": -5.7, "y": 0.7, "theta": 0.0, "scale": 1.0},
                    },
                ],
                "tracks": [
                    {
                        "id": "t_incline",
                        "type": "line",
                        "data": {"part_id": "p_incline", "anchor_a": "start", "anchor_b": "end"},
                    },
                    {
                        "id": "t_flat_left",
                        "type": "line",
                        "data": {"part_id": "p_flat_left", "anchor_a": "start", "anchor_b": "end"},
                    },
                    {
                        "id": "t_arc",
                        "type": "arc",
                        "data": {"cx": 2.0, "cy": -1.2, "r": 1.5, "start_deg": 180.0, "end_deg": 360.0},
                    },
                    {
                        "id": "t_flat_right",
                        "type": "line",
                        "data": {"part_id": "p_flat_right", "anchor_a": "start", "anchor_b": "end"},
                    },
                ],
                "constraints": [
                    {
                        "id": "c_attach_flat_left_to_arc_start",
                        "type": "attach",
                        "args": {
                            "part_a": "p_flat_left",
                            "anchor_a": "end",
                            "part_b": "p_arc",
                            "anchor_b": "start",
                            "mode": "b_to_a",
                            "rigid": True,
                        },
                        "hard": True,
                    },
                    {
                        "id": "c_attach_flat_right_to_arc_end",
                        "type": "attach",
                        "args": {
                            "part_a": "p_flat_right",
                            "anchor_a": "start",
                            "part_b": "p_arc",
                            "anchor_b": "end",
                            "mode": "b_to_a",
                            "rigid": True,
                        },
                        "hard": True,
                    },
                    {
                        "id": "c_attach_incline_to_flat_left",
                        "type": "attach",
                        "args": {
                            "part_a": "p_incline",
                            "anchor_a": "end",
                            "part_b": "p_flat_left",
                            "anchor_b": "start",
                            "mode": "b_to_a",
                            "rigid": True,
                        },
                        "hard": True,
                    },
                    {
                        "id": "c_pose_slider",
                        "type": "on_track_pose",
                        "args": {
                            "part_id": "p_slider",
                            "track_id": "t_incline",
                            "anchor": "bottom_center",
                            "s": 0.0,
                            "angle_mode": "tangent",
                            "contact_side": "outer",
                            "clearance": 0.0,
                        },
                        "hard": True,
                    },
                ],
                "motions": [],
            }
        )

        defaults = ComponentDefaults(font="Arial", text_font_size=30, bullet_font_size=24, formula_font_size=34)
        component_map = build_physics_components()
        part_order = [part.id for part in graph.parts]
        templates: dict[str, object] = {}
        geometries = {}
        for part in graph.parts:
            builder = component_map[part.type]
            spec = ObjectSpec(type=part.type, params=dict(part.params), style={}, priority=1)
            template = builder.build(spec, defaults=defaults)
            template.move_to([0.0, 0.0, 0.0])
            templates[part.id] = template
            geometries[part.id] = geometry_from_mobject(part.id, template)

        rendered = {part_id: templates[part_id].copy() for part_id in part_order}
        self.add(*[rendered[part_id] for part_id in part_order])

        options = SolveOptions(max_iters=120, tolerance=1e-4)
        pose_constraint = next(c for c in graph.constraints if c.id == "c_pose_slider")

        len_incline = 4.0
        len_flat_left = 3.0
        len_arc = math.pi * 1.5
        len_flat_right = 3.0
        total_len = len_incline + len_flat_left + len_arc + len_flat_right
        b1 = len_incline
        b2 = b1 + len_flat_left
        b3 = b2 + len_arc

        def _render_state() -> None:
            result = solve_static(graph, geometries=geometries, options=options)
            for part_id in part_order:
                mobj = templates[part_id].copy()
                _apply_pose(mobj, result.poses[part_id])
                rendered[part_id].become(mobj)

        progress = ValueTracker(0.0)

        def _update(_mobj, _dt: float = 0.0) -> None:
            traveled = float(progress.get_value()) * total_len
            if traveled <= b1:
                track_id = "t_incline"
                s = traveled / max(len_incline, 1e-9)
            elif traveled <= b2:
                track_id = "t_flat_left"
                s = (traveled - b1) / max(len_flat_left, 1e-9)
            elif traveled <= b3:
                track_id = "t_arc"
                s = (traveled - b2) / max(len_arc, 1e-9)
            else:
                track_id = "t_flat_right"
                s = (traveled - b3) / max(len_flat_right, 1e-9)

            pose_constraint.args["track_id"] = track_id
            pose_constraint.args["s"] = float(max(0.0, min(1.0, s)))
            _render_state()

        driver = rendered["p_slider"]
        driver.add_updater(_update)
        _render_state()

        self.wait(0.2)
        self.play(progress.animate(rate_func=linear).set_value(1.0), run_time=8.0)
        driver.remove_updater(_update)
        self.wait(0.4)
