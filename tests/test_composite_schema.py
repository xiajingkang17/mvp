from __future__ import annotations

from pipeline.validate_plan import validate_plan
from schema.scene_plan_models import ScenePlan


def _make_plan_with_object(obj: dict, *, actions: list[dict] | None = None) -> ScenePlan:
    raw = {
        "version": "0.1",
        "meta": {},
        "objects": {"o1": obj},
        "scenes": [
            {
                "id": "S1",
                "layout": {"type": "hero_side", "slots": {"hero": "o1"}, "params": {}},
                "actions": actions or [],
                "keep": [],
            }
        ],
    }
    return ScenePlan.model_validate(raw)


def _valid_graph() -> dict:
    return {
        "version": "0.1",
        "parts": [
            {
                "id": "p1",
                "type": "Wall",
                "params": {"angle": 30, "length": 5.0},
                "style": {},
                "seed_pose": {"x": 0, "y": 0, "theta": 0, "scale": 1.0},
            }
        ],
        "tracks": [{"id": "t1", "type": "segment", "data": {"x1": -2, "y1": 1, "x2": 3, "y2": 0}}],
        "constraints": [{"id": "c1", "type": "on_track_pose", "args": {"part_id": "p1", "track_id": "t1"}, "hard": True}],
        "motions": [],
    }


def test_validate_accepts_composite_object_with_valid_graph():
    plan = _make_plan_with_object(
        {
            "type": "CompositeObject",
            "params": {"graph": _valid_graph()},
            "style": {},
            "priority": 1,
        }
    )
    assert validate_plan(plan) == []


def test_validate_rejects_composite_object_without_graph():
    plan = _make_plan_with_object(
        {
            "type": "CompositeObject",
            "params": {},
            "style": {},
            "priority": 1,
        }
    )
    errors = validate_plan(plan)
    assert any("CompositeObject needs params.graph" in e.message for e in errors)


def test_validate_rejects_recursive_composite_part_type():
    graph = _valid_graph()
    graph["parts"][0]["type"] = "CompositeObject"
    plan = _make_plan_with_object(
        {
            "type": "CompositeObject",
            "params": {"graph": graph},
            "style": {},
            "priority": 1,
        }
    )
    errors = validate_plan(plan)
    assert any(".parts[0].type not allowed: CompositeObject" in e.message for e in errors)


def test_validate_rejects_unknown_physics_params_in_composite_parts():
    graph = _valid_graph()
    graph["parts"][0]["params"]["foo"] = 1
    plan = _make_plan_with_object(
        {
            "type": "CompositeObject",
            "params": {"graph": graph},
            "style": {},
            "priority": 1,
        }
    )
    errors = validate_plan(plan)
    assert any("unknown params" in e.message for e in errors)


def test_validate_rejects_broken_graph_references():
    graph = _valid_graph()
    graph["constraints"][0]["args"]["part_id"] = "missing_part"
    plan = _make_plan_with_object(
        {
            "type": "CompositeObject",
            "params": {"graph": graph},
            "style": {},
            "priority": 1,
        }
    )
    errors = validate_plan(plan)
    assert any("CompositeObject invalid params.graph" in e.message for e in errors)
    assert any("unknown part id" in e.message for e in errors)


def test_validate_rejects_motion_scene_without_explicit_play_duration():
    graph = _valid_graph()
    graph["motions"] = [
        {
            "id": "m1",
            "type": "on_track",
            "args": {"part_id": "p1", "track_id": "t1"},
            "timeline": [{"t": 0.0, "s": 0.0}, {"t": 2.0, "s": 1.0}],
        }
    ]
    plan = _make_plan_with_object(
        {
            "type": "CompositeObject",
            "params": {"graph": graph},
            "style": {},
            "priority": 1,
        },
        actions=[{"op": "play", "anim": "fade_in", "targets": ["o1"]}, {"op": "wait", "duration": 2.2}],
    )
    errors = validate_plan(plan)
    assert any(".duration required when scene has graph.motions" in e.message for e in errors)


def test_validate_rejects_motion_scene_when_action_duration_too_short():
    graph = _valid_graph()
    graph["motions"] = [
        {
            "id": "m1",
            "type": "on_track",
            "args": {"part_id": "p1", "track_id": "t1"},
            "timeline": [{"t": 0.0, "s": 0.0}, {"t": 3.0, "s": 1.0}],
        }
    ]
    plan = _make_plan_with_object(
        {
            "type": "CompositeObject",
            "params": {"graph": graph},
            "style": {},
            "priority": 1,
        },
        actions=[
            {"op": "play", "anim": "fade_in", "targets": ["o1"], "duration": 0.5},
            {"op": "wait", "duration": 0.5},
        ],
    )
    errors = validate_plan(plan)
    assert any("shorter than motion span" in e.message for e in errors)


def test_validate_accepts_motion_scene_with_sufficient_action_duration():
    graph = _valid_graph()
    graph["motions"] = [
        {
            "id": "m1",
            "type": "on_track",
            "args": {"part_id": "p1", "track_id": "t1"},
            "timeline": [{"t": 0.0, "s": 0.0}, {"t": 3.0, "s": 1.0}],
        }
    ]
    plan = _make_plan_with_object(
        {
            "type": "CompositeObject",
            "params": {"graph": graph},
            "style": {},
            "priority": 1,
        },
        actions=[
            {"op": "play", "anim": "fade_in", "targets": ["o1"], "duration": 1.0},
            {"op": "wait", "duration": 2.1},
        ],
    )
    errors = validate_plan(plan)
    assert not any("shorter than motion span" in e.message for e in errors)
    assert not any(".duration required when scene has graph.motions" in e.message for e in errors)
