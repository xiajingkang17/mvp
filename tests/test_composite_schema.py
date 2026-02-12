from __future__ import annotations

from pipeline.validate_plan import validate_plan
from schema.scene_plan_models import ScenePlan


def _make_plan_with_object(obj: dict) -> ScenePlan:
    raw = {
        "version": "0.1",
        "meta": {},
        "objects": {"o1": obj},
        "scenes": [
            {
                "id": "S1",
                "layout": {"type": "hero_side", "slots": {"hero": "o1"}, "params": {}},
                "actions": [],
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
                "type": "InclinedPlane",
                "params": {"angle": 30, "length": 5.0},
                "style": {},
                "seed_pose": {"x": 0, "y": 0, "theta": 0, "scale": 1.0},
            }
        ],
        "tracks": [{"id": "t1", "type": "segment", "data": {"x1": -2, "y1": 1, "x2": 3, "y2": 0}}],
        "constraints": [{"id": "c1", "type": "on_segment", "args": {"part_id": "p1", "track_id": "t1"}, "hard": True}],
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
