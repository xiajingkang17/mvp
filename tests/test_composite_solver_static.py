from __future__ import annotations

import pytest

from render.composite.anchors import default_anchor_map
from render.composite.solver import SolveOptions, solve_static
from render.composite.types import PartGeometry, anchor_world
from schema.composite_graph_models import CompositeGraph


def _geometry(part_id: str, *, w: float = 2.0, h: float = 2.0) -> PartGeometry:
    return PartGeometry(part_id=part_id, anchors=default_anchor_map(width=w, height=h))


def test_solve_static_attach_center():
    graph = CompositeGraph.model_validate(
        {
            "version": "0.1",
            "parts": [
                {"id": "p1", "type": "Block", "seed_pose": {"x": 0.0, "y": 0.0, "theta": 0.0, "scale": 1.0}},
                {"id": "p2", "type": "Block", "seed_pose": {"x": 4.0, "y": 1.0, "theta": 0.0, "scale": 1.0}},
            ],
            "tracks": [],
            "constraints": [{"id": "c1", "type": "attach", "args": {"part_a": "p1", "part_b": "p2"}}],
            "motions": [],
        }
    )
    result = solve_static(
        graph,
        geometries={"p1": _geometry("p1"), "p2": _geometry("p2")},
        options=SolveOptions(max_iters=8, tolerance=1e-6),
    )

    p1 = result.poses["p1"]
    p2 = result.poses["p2"]
    assert p1.x == pytest.approx(p2.x, abs=1e-6)
    assert p1.y == pytest.approx(p2.y, abs=1e-6)
    assert result.unsatisfied_hard() == []


def test_solve_static_on_segment_uses_anchor():
    graph = CompositeGraph.model_validate(
        {
            "version": "0.1",
            "parts": [{"id": "p1", "type": "Block", "seed_pose": {"x": -1.0, "y": 2.0, "theta": 0.0, "scale": 1.0}}],
            "tracks": [{"id": "t1", "type": "segment", "data": {"x1": 0.0, "y1": 0.0, "x2": 10.0, "y2": 0.0}}],
            "constraints": [
                {"id": "c1", "type": "on_segment", "args": {"part_id": "p1", "anchor": "bottom_center", "track_id": "t1", "t": 0.3}}
            ],
            "motions": [],
        }
    )
    geom = _geometry("p1", w=2.0, h=2.0)
    result = solve_static(
        graph,
        geometries={"p1": geom},
        options=SolveOptions(max_iters=8, tolerance=1e-6),
    )
    pose = result.poses["p1"]
    ax, ay = anchor_world(pose, geom.anchor_local("bottom_center"))
    assert ax == pytest.approx(3.0, abs=1e-6)
    assert ay == pytest.approx(0.0, abs=1e-6)


def test_solve_static_midpoint_and_align_axis():
    graph = CompositeGraph.model_validate(
        {
            "version": "0.1",
            "parts": [
                {"id": "pa", "type": "Block", "seed_pose": {"x": 0.0, "y": 0.0}},
                {"id": "pb", "type": "Block", "seed_pose": {"x": 8.0, "y": 2.0}},
                {"id": "pm", "type": "Block", "seed_pose": {"x": 1.0, "y": 4.0}},
            ],
            "tracks": [],
            "constraints": [
                {
                    "id": "c_mid",
                    "type": "midpoint",
                    "args": {"part_id": "pm", "part_1": "pa", "anchor_1": "center", "part_2": "pb", "anchor_2": "center"},
                },
                {"id": "c_align", "type": "align_axis", "args": {"part_a": "pa", "part_b": "pb", "axis": "y", "mode": "both"}},
            ],
            "motions": [],
        }
    )

    geoms = {"pa": _geometry("pa"), "pb": _geometry("pb"), "pm": _geometry("pm")}
    result = solve_static(graph, geometries=geoms, options=SolveOptions(max_iters=40, tolerance=1e-6))

    pa = result.poses["pa"]
    pb = result.poses["pb"]
    pm = result.poses["pm"]

    assert pa.y == pytest.approx(pb.y, abs=1e-6)
    assert pm.x == pytest.approx(0.5 * (pa.x + pb.x), abs=1e-6)
    assert pm.y == pytest.approx(0.5 * (pa.y + pb.y), abs=1e-6)


def test_solve_static_distance():
    graph = CompositeGraph.model_validate(
        {
            "version": "0.1",
            "parts": [
                {"id": "p1", "type": "Block", "seed_pose": {"x": 0.0, "y": 0.0}},
                {"id": "p2", "type": "Block", "seed_pose": {"x": 1.0, "y": 0.0}},
            ],
            "tracks": [],
            "constraints": [{"id": "c1", "type": "distance", "args": {"part_a": "p1", "part_b": "p2", "distance": 5.0}}],
            "motions": [],
        }
    )
    geoms = {"p1": _geometry("p1"), "p2": _geometry("p2")}
    result = solve_static(graph, geometries=geoms, options=SolveOptions(max_iters=8, tolerance=1e-6))

    p1 = result.poses["p1"]
    p2 = result.poses["p2"]
    assert ((p2.x - p1.x) ** 2 + (p2.y - p1.y) ** 2) ** 0.5 == pytest.approx(5.0, abs=1e-6)
