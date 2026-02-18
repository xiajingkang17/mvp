from __future__ import annotations

import math

from manim import Arc, Create, Scene, ValueTracker, linear

from components.physics.mechanics import Block, Wall
from render.composite.anchors import geometry_from_mobject
from render.composite.solver import SolveOptions, solve_static
from schema.composite_graph_models import CompositeGraph


class TestContactMultiSurface(Scene):
    def construct(self):
        incline = Wall(length=4.0, angle=-30)
        incline_line = incline[0]
        incline_bottom_left = incline_line.get_end()
        incline.shift([-6.0 - float(incline_bottom_left[0]), -1.0 - float(incline_bottom_left[1]), 0.0])

        line_points = incline[0]
        p_top_left = line_points.get_start()
        p_bottom_right = line_points.get_end()

        flat1_start = (float(p_bottom_right[0]), float(p_bottom_right[1]))
        arc_center = (3.0, flat1_start[1])
        arc_radius = 2.0
        arc_left = arc_center[0] - arc_radius
        arc_right = arc_center[0] + arc_radius

        flat1_end = (arc_left, flat1_start[1])
        wall1 = Wall(length=flat1_end[0] - flat1_start[0], angle=0)
        wall1.move_to([(flat1_start[0] + flat1_end[0]) * 0.5, flat1_start[1], 0.0])

        arc = Arc(
            radius=arc_radius,
            start_angle=math.pi,
            angle=-math.pi,
        ).move_arc_center_to([arc_center[0], arc_center[1], 0.0])

        flat2_start = (arc_right, flat1_start[1])
        flat2_end = (8.0, flat1_start[1])
        wall2 = Wall(length=flat2_end[0] - flat2_start[0], angle=0)
        wall2.move_to([(flat2_start[0] + flat2_end[0]) * 0.5, flat2_start[1], 0.0])

        block = Block(width=0.85, height=0.55, label="P")
        self.add(incline, wall1, arc, wall2, block)

        graph = CompositeGraph.model_validate(
            {
                "version": "0.1",
                "parts": [{"id": "p_block", "type": "Block", "seed_pose": {"x": float(p_top_left[0]), "y": float(p_top_left[1]), "theta": 0.0, "scale": 1.0}}],
                "tracks": [
                    {
                        "id": "t_incline",
                        "type": "segment",
                        "data": {
                            "x1": float(p_top_left[0]),
                            "y1": float(p_top_left[1]),
                            "x2": float(p_bottom_right[0]),
                            "y2": float(p_bottom_right[1]),
                        },
                    },
                    {"id": "t_flat_1", "type": "segment", "data": {"x1": flat1_start[0], "y1": flat1_start[1], "x2": flat1_end[0], "y2": flat1_end[1]}},
                    {"id": "t_arc", "type": "arc", "data": {"cx": arc_center[0], "cy": arc_center[1], "r": arc_radius, "start_deg": 180.0, "end_deg": 0.0}},
                    {"id": "t_flat_2", "type": "segment", "data": {"x1": flat2_start[0], "y1": flat2_start[1], "x2": flat2_end[0], "y2": flat2_end[1]}},
                ],
                "constraints": [
                    {
                        "id": "c_contact",
                        "type": "on_track_pose",
                        "args": {
                            "part_id": "p_block",
                            "track_id": "t_incline",
                            "anchor": "bottom_center",
                            "s": 0.0,
                            "angle_mode": "tangent",
                        },
                        "hard": True,
                    }
                ],
                "motions": [],
            }
        )

        seg_incline = math.hypot(float(p_bottom_right[0] - p_top_left[0]), float(p_bottom_right[1] - p_top_left[1]))
        seg_flat1 = flat1_end[0] - flat1_start[0]
        seg_arc = math.pi * arc_radius
        seg_flat2 = flat2_end[0] - flat2_start[0]
        total_len = seg_incline + seg_flat1 + seg_arc + seg_flat2

        geom = {"p_block": geometry_from_mobject("p_block", block)}
        options = SolveOptions(max_iters=40, tolerance=1e-6)
        progress = ValueTracker(0.0)
        current_theta = {"deg": 0.0}

        def _update_block(mobj, _dt=0.0):
            traveled = float(progress.get_value()) * total_len
            if traveled <= seg_incline:
                track_id = "t_incline"
                s = traveled / max(seg_incline, 1e-9)
                side = "outer"
            elif traveled <= seg_incline + seg_flat1:
                track_id = "t_flat_1"
                s = (traveled - seg_incline) / max(seg_flat1, 1e-9)
                side = "outer"
            elif traveled <= seg_incline + seg_flat1 + seg_arc:
                track_id = "t_arc"
                s = (traveled - seg_incline - seg_flat1) / max(seg_arc, 1e-9)
                side = "outer"
            else:
                track_id = "t_flat_2"
                s = (traveled - seg_incline - seg_flat1 - seg_arc) / max(seg_flat2, 1e-9)
                side = "outer"

            graph.constraints[0].args["track_id"] = track_id
            graph.constraints[0].args["s"] = float(s)
            graph.constraints[0].args["contact_side"] = side
            result = solve_static(graph, geometries=geom, options=options)
            pose = result.poses["p_block"]
            mobj.move_to([pose.x, pose.y, 0.0])

            delta = float(pose.theta) - float(current_theta["deg"])
            if abs(delta) > 1e-9:
                mobj.rotate(math.radians(delta), about_point=mobj.get_center())
                current_theta["deg"] = float(pose.theta)

        block.add_updater(_update_block)
        self.play(Create(incline), Create(wall1), Create(arc), Create(wall2), run_time=1.8)
        self.play(Create(block), run_time=0.5)
        self.play(progress.animate(rate_func=linear).set_value(1.0), run_time=6.0)
        block.remove_updater(_update_block)
        self.wait(0.4)
