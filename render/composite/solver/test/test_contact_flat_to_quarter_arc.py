from __future__ import annotations

import math

from manim import Arc, Create, Scene, ValueTracker, linear

from components.physics.mechanics import Block, Wall
from render.composite.anchors import geometry_from_mobject
from render.composite.solver import SolveOptions, solve_static
from schema.composite_graph_models import CompositeGraph

DEFAULT_CONTACT_SIDE = "outer"
DEFAULT_CLEARANCE = 0.04


class TestContactFlatToQuarterArc(Scene):
    def construct(self):
        y_ground = -2.0
        x_flat_start = -6.0
        x_flat_end = 0.0
        wall = Wall(length=x_flat_end - x_flat_start, angle=0, contact_offset_y=0.04)
        wall.move_to([(x_flat_start + x_flat_end) * 0.5, y_ground, 0.0])

        radius = 2.2
        arc_center = (x_flat_end, y_ground + radius)
        quarter_arc = Arc(
            radius=radius,
            start_angle=-math.pi / 2.0,
            angle=math.pi / 2.0,
        ).move_arc_center_to([arc_center[0], arc_center[1], 0.0])

        block = Block(width=0.9, height=0.55, label="P")
        self.add(wall, quarter_arc, block)

        graph = CompositeGraph.model_validate(
            {
                "version": "0.1",
                "parts": [{"id": "p_block", "type": "Block", "seed_pose": {"x": x_flat_start, "y": y_ground, "theta": 0.0, "scale": 1.0}}],
                "tracks": [
                    {"id": "t_flat", "type": "segment", "data": {"x1": x_flat_start, "y1": y_ground, "x2": x_flat_end, "y2": y_ground}},
                    {
                        "id": "t_arc",
                        "type": "arc",
                        "data": {"cx": arc_center[0], "cy": arc_center[1], "r": radius, "start_deg": -90.0, "end_deg": 0.0},
                    },
                ],
                "constraints": [
                    {
                        "id": "c_contact",
                        "type": "on_track_pose",
                        "args": {
                            "part_id": "p_block",
                            "track_id": "t_flat",
                            "anchor": "bottom_center",
                            "s": 0.0,
                            "angle_mode": "tangent",
                            "contact_side": DEFAULT_CONTACT_SIDE,
                            "clearance": DEFAULT_CLEARANCE,
                        },
                        "hard": True,
                    },
                ],
                "motions": [],
            }
        )

        flat_len = x_flat_end - x_flat_start
        arc_len = (math.pi / 2.0) * radius
        total_len = flat_len + arc_len

        geom = {"p_block": geometry_from_mobject("p_block", block)}
        options = SolveOptions(max_iters=40, tolerance=1e-6)
        progress = ValueTracker(0.0)
        current_theta = {"deg": 0.0}

        def _update_block(mobj, _dt=0.0):
            traveled = float(progress.get_value()) * total_len
            if traveled <= flat_len:
                track_id = "t_flat"
                s = traveled / max(flat_len, 1e-9)
            else:
                track_id = "t_arc"
                s = (traveled - flat_len) / max(arc_len, 1e-9)
                track_point_tangent("arc", graph.tracks[1].data, float(s))

            graph.constraints[0].args["track_id"] = track_id
            graph.constraints[0].args["s"] = float(s)
            graph.constraints[0].args["contact_side"] = DEFAULT_CONTACT_SIDE
            graph.constraints[0].args["angle_mode"] = "tangent"

            result = solve_static(graph, geometries=geom, options=options)
            pose = result.poses["p_block"]
            mobj.move_to([pose.x, pose.y, 0.0])

            delta = float(pose.theta) - float(current_theta["deg"])
            if abs(delta) > 1e-9:
                mobj.rotate(math.radians(delta), about_point=mobj.get_center())
                current_theta["deg"] = float(pose.theta)

        block.add_updater(_update_block)
        self.play(Create(wall), Create(quarter_arc), run_time=1.4)
        self.play(Create(block), run_time=0.5)
        self.play(progress.animate(rate_func=linear).set_value(1.0), run_time=5.0)
        block.remove_updater(_update_block)
        self.wait(0.4)
