from __future__ import annotations

import json
from pathlib import Path

from pipeline.validate_plan import validate_plan
from schema.scene_plan_models import ScenePlan


def test_demo_plan_validates():
    plan_path = Path("cases/demo_001/scene_plan.json")
    raw = json.loads(plan_path.read_text(encoding="utf-8"))
    plan = ScenePlan.model_validate(raw)
    errors = validate_plan(plan)
    assert errors == []

