from __future__ import annotations

import pytest

from render.composite.anchors import default_anchor_map
from render.composite.motion import apply_motions, evaluate_timeline
from render.composite.types import PartGeometry, Pose, anchor_world
from schema.composite_graph_models import CompositeGraph


def _graph_with_track(track_data: dict, *, theta_mode: str = "keep") -> CompositeGraph:
    return CompositeGraph.model_validate(
        {
            "version": "0.1",
            "parts": [{"id": "p1", "type": "Block", "seed_pose": {"x": 0.0, "y": 0.0, "theta": 0.0, "scale": 1.0}}],
            "tracks": [{"id": "t1", "type": "segment", "data": track_data}],
            "constraints": [],
            "motions": [
                {
                    "id": "m1",
                    "type": "on_track",
                    "args": {"part_id": "p1", "anchor": "bottom_center", "track_id": "t1", "theta_mode": theta_mode},
                    "timeline": [{"t": 0.0, "s": 0.0}, {"t": 2.0, "s": 1.0}],
                }
            ],
        }
    )


def test_evaluate_timeline_linear_interpolation():
    timeline = [{"t": 0.0, "s": 0.0}, {"t": 2.0, "s": 1.0}]
    assert evaluate_timeline(timeline, -1.0) == pytest.approx(0.0, abs=1e-9)
    assert evaluate_timeline(timeline, 1.0) == pytest.approx(0.5, abs=1e-9)
    assert evaluate_timeline(timeline, 3.0) == pytest.approx(1.0, abs=1e-9)


def test_apply_motion_on_track_uses_anchor_contact():
    graph = _graph_with_track({"x1": 0.0, "y1": 0.0, "x2": 10.0, "y2": 0.0})
    geom = PartGeometry(part_id="p1", anchors=default_anchor_map(width=2.0, height=2.0))
    poses = {"p1": Pose(x=0.0, y=0.0, theta=0.0, scale=1.0)}

    updated = apply_motions(graph, poses=poses, geometries={"p1": geom}, time_value=1.0)

    anchor = anchor_world(updated["p1"], geom.anchor_local("bottom_center"))
    assert anchor[0] == pytest.approx(5.0, abs=1e-6)
    assert anchor[1] == pytest.approx(0.0, abs=1e-6)
    # Since anchor is bottom_center (0, -1), center should be y=1 above a horizontal track.
    assert updated["p1"].y == pytest.approx(1.0, abs=1e-6)


def test_apply_motion_on_track_theta_mode_tangent():
    graph = _graph_with_track({"x1": 2.0, "y1": 0.0, "x2": 2.0, "y2": 10.0}, theta_mode="tangent")
    geom = PartGeometry(part_id="p1", anchors=default_anchor_map(width=2.0, height=2.0))
    poses = {"p1": Pose(x=0.0, y=0.0, theta=0.0, scale=1.0)}

    updated = apply_motions(graph, poses=poses, geometries={"p1": geom}, time_value=1.0)
    assert updated["p1"].theta == pytest.approx(90.0, abs=1e-6)
