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


def test_validate_accepts_known_physics_object_params():
    plan = _make_plan_with_object(
        {
            "type": "Wall",
            "params": {"angle": 30, "length": 5.0, "hatch_spacing": 0.4},
            "style": {"size_level": "L"},
            "priority": 1,
        }
    )
    assert validate_plan(plan) == []


def test_validate_rejects_unknown_physics_object_params():
    plan = _make_plan_with_object(
        {
            "type": "Wall",
            "params": {"angle": 30, "foo": 1},
            "style": {"size_level": "L"},
            "priority": 1,
        }
    )
    errors = validate_plan(plan)
    assert any("unknown params" in e.message for e in errors)

