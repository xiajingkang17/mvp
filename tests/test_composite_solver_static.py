from __future__ import annotations

import pytest

from render.composite.anchors import default_anchor_map
from render.composite.solver import SolveOptions, solve_static
from render.composite.types import PartGeometry, anchor_world
from schema.composite_graph_models import CompositeGraph


def _geometry(part_id: str, *, w: float = 2.0, h: float = 2.0) -> PartGeometry:
    half_w = 0.5 * float(w)
    half_h = 0.5 * float(h)
    anchors = dict(default_anchor_map(width=w, height=h))
    anchors.update(
        {
            "bottom_center": (0.0, -half_h),
            "top_center": (0.0, half_h),
            "left_center": (-half_w, 0.0),
            "right_center": (half_w, 0.0),
            "start": (-half_w, 0.0),
            "end": (half_w, 0.0),
        }
    )
    return PartGeometry(part_id=part_id, anchors=anchors)


def _rod_geometry(part_id: str, *, half_len: float = 1.0) -> PartGeometry:
    return PartGeometry(
        part_id=part_id,
        anchors={
            "center": (0.0, 0.0),
            "start": (-half_len, 0.0),
            "end": (half_len, 0.0),
        },
    )


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


def test_solve_static_rigid_attach_chain_moves_as_welded_group():
    graph = CompositeGraph.model_validate(
        {
            "version": "0.1",
            "parts": [
                {"id": "p1", "type": "Rod", "seed_pose": {"x": 0.0, "y": 0.0, "theta": 0.0, "scale": 1.0}},
                {"id": "p2", "type": "Rod", "seed_pose": {"x": 2.0, "y": 0.0, "theta": 0.0, "scale": 1.0}},
                {"id": "p3", "type": "Rod", "seed_pose": {"x": 4.0, "y": 0.0, "theta": 0.0, "scale": 1.0}},
            ],
            "tracks": [],
            "constraints": [
                {
                    "id": "c12",
                    "type": "attach",
                    "args": {
                        "part_a": "p1",
                        "anchor_a": "end",
                        "part_b": "p2",
                        "anchor_b": "start",
                        "mode": "b_to_a",
                        "rigid": True,
                    },
                },
                {
                    "id": "c23",
                    "type": "attach",
                    "args": {
                        "part_a": "p2",
                        "anchor_a": "end",
                        "part_b": "p3",
                        "anchor_b": "start",
                        "mode": "b_to_a",
                        "rigid": True,
                    },
                },
                {
                    "id": "c_drive",
                    "type": "midpoint",
                    "args": {"part_id": "p2", "anchor": "center", "point_1": [10.0, 0.0], "point_2": [10.0, 0.0]},
                },
            ],
            "motions": [],
        }
    )
    geoms = {"p1": _rod_geometry("p1"), "p2": _rod_geometry("p2"), "p3": _rod_geometry("p3")}
    result = solve_static(graph, geometries=geoms, options=SolveOptions(max_iters=20, tolerance=1e-6))

    assert result.poses["p1"].theta == pytest.approx(0.0, abs=1e-6)
    assert result.poses["p2"].theta == pytest.approx(0.0, abs=1e-6)
    assert result.poses["p3"].theta == pytest.approx(0.0, abs=1e-6)
    assert result.poses["p2"].x == pytest.approx(10.0, abs=1e-6)
    assert result.poses["p2"].y == pytest.approx(0.0, abs=1e-6)

    p1_end = anchor_world(result.poses["p1"], geoms["p1"].anchor_local("end"))
    p2_start = anchor_world(result.poses["p2"], geoms["p2"].anchor_local("start"))
    p2_end = anchor_world(result.poses["p2"], geoms["p2"].anchor_local("end"))
    p3_start = anchor_world(result.poses["p3"], geoms["p3"].anchor_local("start"))
    assert p1_end[0] == pytest.approx(p2_start[0], abs=1e-6)
    assert p1_end[1] == pytest.approx(p2_start[1], abs=1e-6)
    assert p2_end[0] == pytest.approx(p3_start[0], abs=1e-6)
    assert p2_end[1] == pytest.approx(p3_start[1], abs=1e-6)
    assert result.unsatisfied_hard() == []


def test_solve_static_on_track_pose_uses_anchor():
    graph = CompositeGraph.model_validate(
        {
            "version": "0.1",
            "parts": [{"id": "p1", "type": "Block", "seed_pose": {"x": -1.0, "y": 2.0, "theta": 0.0, "scale": 1.0}}],
            "tracks": [{"id": "t1", "type": "segment", "data": {"x1": 0.0, "y1": 0.0, "x2": 10.0, "y2": 0.0}}],
            "constraints": [
                {"id": "c1", "type": "on_track_pose", "args": {"part_id": "p1", "anchor": "bottom_center", "track_id": "t1", "t": 0.3, "angle_mode": "keep"}}
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


def test_solve_static_midpoint():
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
                }
            ],
            "motions": [],
        }
    )

    geoms = {"pa": _geometry("pa"), "pb": _geometry("pb"), "pm": _geometry("pm")}
    result = solve_static(graph, geometries=geoms, options=SolveOptions(max_iters=40, tolerance=1e-6))

    pa = result.poses["pa"]
    pb = result.poses["pb"]
    pm = result.poses["pm"]

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


def test_solve_static_on_track_pose_segment_with_tangent_orientation():
    graph = CompositeGraph.model_validate(
        {
            "version": "0.1",
            "parts": [{"id": "p1", "type": "Block", "seed_pose": {"x": -2.0, "y": 3.0, "theta": 0.0, "scale": 1.0}}],
            "tracks": [{"id": "t1", "type": "segment", "data": {"x1": 0.0, "y1": 0.0, "x2": 4.0, "y2": 4.0}}],
            "constraints": [
                {
                    "id": "c1",
                    "type": "on_track_pose",
                    "args": {"part_id": "p1", "anchor": "bottom_center", "track_id": "t1", "s": 0.5, "angle_mode": "tangent"},
                }
            ],
            "motions": [],
        }
    )
    geom = _geometry("p1", w=2.0, h=2.0)
    result = solve_static(graph, geometries={"p1": geom}, options=SolveOptions(max_iters=8, tolerance=1e-6))
    pose = result.poses["p1"]
    ax, ay = anchor_world(pose, geom.anchor_local("bottom_center"))
    assert ax == pytest.approx(2.0, abs=1e-6)
    assert ay == pytest.approx(2.0, abs=1e-6)
    assert pose.theta == pytest.approx(45.0, abs=1e-6)


def test_solve_static_on_track_pose_arc_with_offset():
    graph = CompositeGraph.model_validate(
        {
            "version": "0.1",
            "parts": [{"id": "p1", "type": "Block", "seed_pose": {"x": 0.0, "y": 0.0, "theta": 0.0, "scale": 1.0}}],
            "tracks": [{"id": "t1", "type": "arc", "data": {"cx": 0.0, "cy": 0.0, "r": 5.0, "start_deg": 0.0, "end_deg": 180.0}}],
            "constraints": [
                {
                    "id": "c1",
                    "type": "on_track_pose",
                    "args": {"part_id": "p1", "anchor": "bottom_center", "track_id": "t1", "s": 0.5, "clearance": 1.0},
                }
            ],
            "motions": [],
        }
    )
    geom = _geometry("p1", w=2.0, h=2.0)
    result = solve_static(graph, geometries={"p1": geom}, options=SolveOptions(max_iters=8, tolerance=1e-6))
    pose = result.poses["p1"]

    # s=0.5 on 0..180 arc => top point (0,5), outer side points away from center => (0,6)
    ax, ay = anchor_world(pose, geom.anchor_local("bottom_center"))
    assert ax == pytest.approx(0.0, abs=1e-6)
    assert ay == pytest.approx(6.0, abs=1e-6)
    assert pose.theta == pytest.approx(180.0, abs=1e-6)


def test_solve_static_on_track_pose_contact_side_inner_outer():
    base_graph = {
        "version": "0.1",
        "parts": [{"id": "p1", "type": "Block", "seed_pose": {"x": 0.0, "y": 0.0, "theta": 0.0, "scale": 1.0}}],
        "tracks": [{"id": "t1", "type": "segment", "data": {"x1": 0.0, "y1": 0.0, "x2": 4.0, "y2": 0.0}}],
        "constraints": [],
        "motions": [],
    }
    geom = _geometry("p1", w=2.0, h=2.0)

    outer_graph = dict(base_graph)
    outer_graph["constraints"] = [
        {
            "id": "c_outer",
            "type": "on_track_pose",
            "args": {
                "part_id": "p1",
                "anchor": "bottom_center",
                "track_id": "t1",
                "s": 0.5,
                "clearance": 1.0,
                "contact_side": "outer",
            },
        }
    ]
    outer = solve_static(
        CompositeGraph.model_validate(outer_graph),
        geometries={"p1": geom},
        options=SolveOptions(max_iters=8, tolerance=1e-6),
    )
    outer_anchor = anchor_world(outer.poses["p1"], geom.anchor_local("bottom_center"))
    assert outer_anchor[0] == pytest.approx(2.0, abs=1e-6)
    assert outer_anchor[1] == pytest.approx(1.0, abs=1e-6)

    inner_graph = dict(base_graph)
    inner_graph["constraints"] = [
        {
            "id": "c_inner",
            "type": "on_track_pose",
            "args": {
                "part_id": "p1",
                "anchor": "bottom_center",
                "track_id": "t1",
                "s": 0.5,
                "clearance": 1.0,
                "contact_side": "inner",
            },
        }
    ]
    inner = solve_static(
        CompositeGraph.model_validate(inner_graph),
        geometries={"p1": geom},
        options=SolveOptions(max_iters=8, tolerance=1e-6),
    )
    inner_anchor = anchor_world(inner.poses["p1"], geom.anchor_local("bottom_center"))
    assert inner_anchor[0] == pytest.approx(2.0, abs=1e-6)
    assert inner_anchor[1] == pytest.approx(-1.0, abs=1e-6)


def test_solve_static_on_track_pose_tangent():
    graph = CompositeGraph.model_validate(
        {
            "version": "0.1",
            "parts": [{"id": "p1", "type": "Block", "seed_pose": {"x": 0.0, "y": 0.0, "theta": 0.0, "scale": 1.0}}],
            "tracks": [{"id": "t1", "type": "segment", "data": {"x1": 0.0, "y1": 0.0, "x2": 4.0, "y2": 4.0}}],
            "constraints": [
                {
                    "id": "c1",
                    "type": "on_track_pose",
                    "args": {"part_id": "p1", "track_id": "t1", "anchor": "bottom_center", "s": 0.25, "angle_mode": "tangent"},
                }
            ],
            "motions": [],
        }
    )
    geom = _geometry("p1", w=2.0, h=2.0)
    result = solve_static(graph, geometries={"p1": geom}, options=SolveOptions(max_iters=8, tolerance=1e-6))
    pose = result.poses["p1"]
    anchor = anchor_world(pose, geom.anchor_local("bottom_center"))
    assert anchor[0] == pytest.approx(1.0, abs=1e-6)
    assert anchor[1] == pytest.approx(1.0, abs=1e-6)
    assert pose.theta == pytest.approx(45.0, abs=1e-6)


def test_solve_static_on_track_pose_fixed_angle():
    graph = CompositeGraph.model_validate(
        {
            "version": "0.1",
            "parts": [{"id": "p1", "type": "Block", "seed_pose": {"x": 2.0, "y": 1.0, "theta": -10.0, "scale": 1.0}}],
            "tracks": [{"id": "t1", "type": "segment", "data": {"x1": 0.0, "y1": 0.0, "x2": 5.0, "y2": 0.0}}],
            "constraints": [
                {
                    "id": "c1",
                    "type": "on_track_pose",
                    "args": {"part_id": "p1", "track_id": "t1", "anchor": "bottom_center", "s": 0.4, "angle_mode": "fixed", "angle": 20.0},
                }
            ],
            "motions": [],
        }
    )
    geom = _geometry("p1", w=2.0, h=2.0)
    result = solve_static(graph, geometries={"p1": geom}, options=SolveOptions(max_iters=8, tolerance=1e-6))
    pose = result.poses["p1"]
    anchor = anchor_world(pose, geom.anchor_local("bottom_center"))
    assert anchor[0] == pytest.approx(2.0, abs=1e-6)
    assert anchor[1] == pytest.approx(0.0, abs=1e-6)
    assert pose.theta == pytest.approx(20.0, abs=1e-6)


def test_solve_static_on_track_pose_arc_inner_outer():
    base = {
        "version": "0.1",
        "parts": [{"id": "p1", "type": "Block", "seed_pose": {"x": 0.0, "y": 0.0, "theta": 0.0, "scale": 1.0}}],
        "tracks": [{"id": "t1", "type": "arc", "data": {"cx": 0.0, "cy": 0.0, "r": 3.0, "start_deg": 0.0, "end_deg": 180.0}}],
        "constraints": [],
        "motions": [],
    }
    geom = _geometry("p1", w=2.0, h=2.0)

    outer_graph = dict(base)
    outer_graph["constraints"] = [
        {
            "id": "c1",
            "type": "on_track_pose",
            "args": {
                "part_id": "p1",
                "track_id": "t1",
                "anchor": "bottom_center",
                "s": 0.5,
                "clearance": 1.0,
                "contact_side": "outer",
            },
        }
    ]
    outer = solve_static(CompositeGraph.model_validate(outer_graph), geometries={"p1": geom}, options=SolveOptions(max_iters=8, tolerance=1e-6))
    outer_anchor = anchor_world(outer.poses["p1"], geom.anchor_local("bottom_center"))
    assert outer_anchor[0] == pytest.approx(0.0, abs=1e-6)
    assert outer_anchor[1] == pytest.approx(4.0, abs=1e-6)

    inner_graph = dict(base)
    inner_graph["constraints"] = [
        {
            "id": "c1",
            "type": "on_track_pose",
            "args": {
                "part_id": "p1",
                "track_id": "t1",
                "anchor": "bottom_center",
                "s": 0.5,
                "clearance": 1.0,
                "contact_side": "inner",
            },
        }
    ]
    inner = solve_static(CompositeGraph.model_validate(inner_graph), geometries={"p1": geom}, options=SolveOptions(max_iters=8, tolerance=1e-6))
    inner_anchor = anchor_world(inner.poses["p1"], geom.anchor_local("bottom_center"))
    assert inner_anchor[0] == pytest.approx(0.0, abs=1e-6)
    assert inner_anchor[1] == pytest.approx(2.0, abs=1e-6)


def test_solve_static_on_track_pose_clearance_monotonic():
    base = {
        "version": "0.1",
        "parts": [{"id": "p1", "type": "Block", "seed_pose": {"x": 0.0, "y": 0.0, "theta": 0.0, "scale": 1.0}}],
        "tracks": [{"id": "t1", "type": "segment", "data": {"x1": 0.0, "y1": 0.0, "x2": 4.0, "y2": 0.0}}],
        "constraints": [],
        "motions": [],
    }
    geom = _geometry("p1", w=2.0, h=2.0)

    graph_small = dict(base)
    graph_small["constraints"] = [
        {
            "id": "c1",
            "type": "on_track_pose",
            "args": {"part_id": "p1", "track_id": "t1", "anchor": "bottom_center", "s": 0.5, "clearance": 0.02},
        }
    ]
    small = solve_static(CompositeGraph.model_validate(graph_small), geometries={"p1": geom}, options=SolveOptions(max_iters=8, tolerance=1e-6))
    y_small = anchor_world(small.poses["p1"], geom.anchor_local("bottom_center"))[1]

    graph_large = dict(base)
    graph_large["constraints"] = [
        {
            "id": "c1",
            "type": "on_track_pose",
            "args": {"part_id": "p1", "track_id": "t1", "anchor": "bottom_center", "s": 0.5, "clearance": 0.08},
        }
    ]
    large = solve_static(CompositeGraph.model_validate(graph_large), geometries={"p1": geom}, options=SolveOptions(max_iters=8, tolerance=1e-6))
    y_large = anchor_world(large.poses["p1"], geom.anchor_local("bottom_center"))[1]
    assert y_large > y_small


def test_solve_static_on_track_pose_default_clearance_zero():
    graph = CompositeGraph.model_validate(
        {
            "version": "0.1",
            "parts": [{"id": "p1", "type": "Block", "seed_pose": {"x": 0.0, "y": 0.0, "theta": 0.0, "scale": 1.0}}],
            "tracks": [{"id": "t1", "type": "segment", "data": {"x1": 0.0, "y1": 0.0, "x2": 4.0, "y2": 0.0}}],
            "constraints": [
                {
                    "id": "c1",
                    "type": "on_track_pose",
                    "args": {"part_id": "p1", "track_id": "t1", "anchor": "bottom_center", "s": 0.5},
                }
            ],
            "motions": [],
        }
    )
    geom = _geometry("p1", w=2.0, h=2.0)
    result = solve_static(graph, geometries={"p1": geom}, options=SolveOptions(max_iters=8, tolerance=1e-6))
    anchor = anchor_world(result.poses["p1"], geom.anchor_local("bottom_center"))
    assert anchor[1] == pytest.approx(0.0, abs=1e-6)
