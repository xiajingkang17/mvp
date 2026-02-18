from __future__ import annotations

import math

from manim import Arc, Create, Scene, ValueTracker, linear

from components.physics.mechanics import Block
from render.composite.anchors import geometry_from_mobject
from render.composite.solver import SolveOptions, solve_static
from schema.composite_graph_models import CompositeGraph


class TestContactOnArc(Scene):
    def construct(self):
        center_x, center_y = 0.0, -1.0
        radius = 3.0
        start_deg, end_deg = 20.0, 160.0

        arc = Arc(
            radius=radius,
            start_angle=math.radians(start_deg),
            angle=math.radians(end_deg - start_deg),
        ).move_arc_center_to([center_x, center_y, 0.0])

        block = Block(width=0.8, height=0.5, label="P")
        self.add(arc, block)

        graph = CompositeGraph.model_validate(
            {
                "version": "0.1",
                "parts": [{"id": "p_block", "type": "Block", "seed_pose": {"x": 0.0, "y": 2.0, "theta": 0.0, "scale": 1.0}}],
                "tracks": [
                    {
                        "id": "t_arc",
                        "type": "arc",
                        "data": {
                            "cx": center_x,
                            "cy": center_y,
                            "r": radius,
                            "start_deg": start_deg,
                            "end_deg": end_deg,
                        },
                    }
                ],
                "constraints": [
                    {
                        "id": "c_contact",
                        "type": "on_track_pose",
                        "args": {
                            "part_id": "p_block",
                            "track_id": "t_arc",
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

        self.play(Create(arc), run_time=1.2)
        self.play(Create(block), run_time=0.6)
        self.play(s_tracker.animate(rate_func=linear).set_value(1.0), run_time=3.0)
        block.remove_updater(_update_block)
        self.wait(0.3)
