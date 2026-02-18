from __future__ import annotations

import math

from manim import Create, Scene, ValueTracker, linear

from components.physics.mechanics import Block, Wall
from render.composite.anchors import geometry_from_mobject
from render.composite.solver import SolveOptions, solve_static
from schema.composite_graph_models import CompositeGraph


class TestContactOnIncline(Scene):
    def construct(self):
        angle_deg = 37.0
        length = 6.0
        incline = Wall(length=length, angle=-angle_deg)
        incline.move_to([-2.5, -2.0, 0.0])
        line = incline[0]
        p_top_left = line.get_start()
        p_bottom_right = line.get_end()

        block = Block(width=0.9, height=0.6, label="P")
        self.add(incline, block)

        graph = CompositeGraph.model_validate(
            {
                "version": "0.1",
                "parts": [{"id": "p_block", "type": "Block", "seed_pose": {"x": -3.0, "y": 0.0, "theta": 0.0, "scale": 1.0}}],
                "tracks": [
                    {
                        "id": "t_slope",
                        "type": "segment",
                        "data": {
                            "x1": float(p_top_left[0]),
                            "y1": float(p_top_left[1]),
                            "x2": float(p_bottom_right[0]),
                            "y2": float(p_bottom_right[1]),
                        },
                    }
                ],
                "constraints": [
                    {
                        "id": "c_contact",
                        "type": "on_track_pose",
                        "args": {
                            "part_id": "p_block",
                            "track_id": "t_slope",
                            "anchor": "bottom_center",
                            "s": 0.0,
                            "angle_mode": "tangent",
                            "clearance": 0.0,
                        },
                        "hard": True,
                    }
                ],
                "motions": [],
            }
        )
        geom = {"p_block": geometry_from_mobject("p_block", block)}
        options = SolveOptions(max_iters=30, tolerance=1e-6)

        s_tracker = ValueTracker(0.0)
        current_theta = {"deg": 0.0}

        def _update_block(_mobj, _dt=0.0):
            graph.constraints[0].args["s"] = float(s_tracker.get_value())
            result = solve_static(graph, geometries=geom, options=options)
            pose = result.poses["p_block"]
            _mobj.move_to([pose.x, pose.y, 0.0])
            delta = float(pose.theta) - float(current_theta["deg"])
            if abs(delta) > 1e-9:
                _mobj.rotate(math.radians(delta), about_point=_mobj.get_center())
                current_theta["deg"] = float(pose.theta)

        block.add_updater(_update_block)

        self.play(Create(incline), run_time=1.2)
        self.play(Create(block), run_time=0.6)
        self.play(s_tracker.animate(rate_func=linear).set_value(1.0), run_time=3.0)
        block.remove_updater(_update_block)
        self.wait(0.3)
