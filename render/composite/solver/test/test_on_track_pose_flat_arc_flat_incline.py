from __future__ import annotations

import math

from manim import Arc, Create, Scene, ValueTracker, linear

from components.physics.mechanics import Block, Wall
from render.composite.anchors import geometry_from_mobject
from render.composite.solver import SolveOptions, solve_static
from schema.composite_graph_models import CompositeGraph

DEFAULT_CONTACT_SIDE = "outer"
DEFAULT_CLEARANCE = 0.04


class TestOnTrackPoseFlatArcFlatIncline(Scene):
    def construct(self):
        y_ground = -2.0

        # Segment 1: flat ground
        flat1_start = (-8.0, y_ground)
        flat1_end = (-3.0, y_ground)
        wall1 = Wall(length=flat1_end[0] - flat1_start[0], angle=0, contact_offset_y=0.04)
        wall1.move_to([(flat1_start[0] + flat1_end[0]) * 0.5, y_ground, 0.0])

        # Segment 2: upper semicircle, connected to flat ends
        arc_center = (-1.0, y_ground)
        arc_radius = 2.0
        arc = Arc(radius=arc_radius, start_angle=math.pi, angle=-math.pi).move_arc_center_to(
            [arc_center[0], arc_center[1], 0.0]
        )
        arc_left = (arc_center[0] - arc_radius, y_ground)
        arc_right = (arc_center[0] + arc_radius, y_ground)

        # Segment 3: flat ground
        flat2_start = arc_right
        flat2_end = (5.0, y_ground)
        wall2 = Wall(length=flat2_end[0] - flat2_start[0], angle=0, contact_offset_y=0.04)
        wall2.move_to([(flat2_start[0] + flat2_end[0]) * 0.5, y_ground, 0.0])

        # Segment 4: incline (connected at bottom-right to flat2_end)
        incline = Wall(length=4.0, angle=-30)
        incline_line = incline[0]
        bottom_right_local = incline_line.get_end()
        incline.shift(
            [
                flat2_end[0] - float(bottom_right_local[0]),
                y_ground - float(bottom_right_local[1]),
                0.0,
            ]
        )
        slope_line = incline[0]
        slope_top_left = (float(slope_line.get_start()[0]), float(slope_line.get_start()[1]))
        slope_bottom_right = (float(slope_line.get_end()[0]), float(slope_line.get_end()[1]))

        block = Block(width=0.9, height=0.55, label="P")
        self.add(wall1, arc, wall2, incline, block)

        graph = CompositeGraph.model_validate(
            {
                "version": "0.1",
                "parts": [
                    {
                        "id": "p_block",
                        "type": "Block",
                        "seed_pose": {
                            "x": flat1_start[0],
                            "y": flat1_start[1],
                            "theta": 0.0,
                            "scale": 1.0,
                        },
                    }
                ],
                "tracks": [
                    {
                        "id": "t_flat1",
                        "type": "segment",
                        "data": {"x1": flat1_start[0], "y1": flat1_start[1], "x2": flat1_end[0], "y2": flat1_end[1]},
                    },
                    {
                        "id": "t_arc",
                        "type": "arc",
                        "data": {"cx": arc_center[0], "cy": arc_center[1], "r": arc_radius, "start_deg": 180.0, "end_deg": 0.0},
                    },
                    {
                        "id": "t_flat2",
                        "type": "segment",
                        "data": {"x1": flat2_start[0], "y1": flat2_start[1], "x2": flat2_end[0], "y2": flat2_end[1]},
                    },
                    {
                        "id": "t_incline",
                        "type": "segment",
                        "data": {
                            "x1": slope_top_left[0],
                            "y1": slope_top_left[1],
                            "x2": slope_bottom_right[0],
                            "y2": slope_bottom_right[1],
                        },
                    },
                ],
                "constraints": [
                    {
                        "id": "c_track_pose",
                        "type": "on_track_pose",
                        "args": {
                            "part_id": "p_block",
                            "track_id": "t_flat1",
                            "anchor": "bottom_center",
                            "s": 0.0,
                            "angle_mode": "tangent",
                            "contact_side": DEFAULT_CONTACT_SIDE,
                            "clearance": DEFAULT_CLEARANCE,
                        },
                        "hard": True,
                    }
                ],
                "motions": [],
            }
        )

        len_flat1 = flat1_end[0] - flat1_start[0]
        len_arc = math.pi * arc_radius
        len_flat2 = flat2_end[0] - flat2_start[0]
        len_incline = math.hypot(slope_bottom_right[0] - slope_top_left[0], slope_bottom_right[1] - slope_top_left[1])
        total_len = len_flat1 + len_arc + len_flat2 + len_incline

        geom = {"p_block": geometry_from_mobject("p_block", block)}
        options = SolveOptions(max_iters=40, tolerance=1e-6)
        progress = ValueTracker(0.0)
        current_theta = {"deg": 0.0}

        def _update_block(mobj, _dt=0.0):
            traveled = float(progress.get_value()) * total_len
            if traveled <= len_flat1:
                track_id = "t_flat1"
                s = traveled / max(len_flat1, 1e-9)
            elif traveled <= len_flat1 + len_arc:
                track_id = "t_arc"
                s = (traveled - len_flat1) / max(len_arc, 1e-9)
            elif traveled <= len_flat1 + len_arc + len_flat2:
                track_id = "t_flat2"
                s = (traveled - len_flat1 - len_arc) / max(len_flat2, 1e-9)
            else:
                track_id = "t_incline"
                # Enter incline from bottom-right, so reverse track parameter.
                local = (traveled - len_flat1 - len_arc - len_flat2) / max(len_incline, 1e-9)
                s = 1.0 - local

            graph.constraints[0].args["track_id"] = track_id
            graph.constraints[0].args["s"] = float(s)
            graph.constraints[0].args["contact_side"] = DEFAULT_CONTACT_SIDE

            result = solve_static(graph, geometries=geom, options=options)
            pose = result.poses["p_block"]
            mobj.move_to([pose.x, pose.y, 0.0])

            delta = float(pose.theta) - float(current_theta["deg"])
            if abs(delta) > 1e-9:
                mobj.rotate(math.radians(delta), about_point=mobj.get_center())
                current_theta["deg"] = float(pose.theta)

        block.add_updater(_update_block)
        self.play(Create(wall1), Create(arc), Create(wall2), Create(incline), run_time=1.8)
        self.play(Create(block), run_time=0.5)
        self.play(progress.animate(rate_func=linear).set_value(1.0), run_time=7.0)
        block.remove_updater(_update_block)
        self.wait(0.4)
