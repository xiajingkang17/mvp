from __future__ import annotations

import json

from components.base import ComponentDefaults
from components.common.custom_object import CustomObjectComponent
from pipeline.validate_plan import validate_plan
from schema.scene_plan_models import ObjectSpec, ScenePlan


def test_custom_object_component_build_and_time_update(tmp_path, monkeypatch):
    case_dir = tmp_path / "case"
    case_dir.mkdir(parents=True, exist_ok=True)

    code_path = case_dir / "llm_codegen.py"
    code_path.write_text(
        "\n".join(
            [
                "from manim import Dot, VGroup",
                "",
                "def build_moving_dot(spec):",
                "    return VGroup(Dot([0.0, 0.0, 0.0]))",
                "",
                "def update_moving_dot(mobj, t, spec):",
                "    mobj.submobjects[0].move_to([float(t), 0.0, 0.0])",
                "",
                "BUILDERS = {'moving_dot': build_moving_dot}",
                "UPDATERS = {'moving_dot': update_moving_dot}",
            ]
        ),
        encoding="utf-8",
    )

    plan_path = case_dir / "scene_plan.json"
    plan_path.write_text("{}", encoding="utf-8")
    monkeypatch.setenv("SCENE_PLAN", str(plan_path))

    spec = ObjectSpec(type="CustomObject", params={"code_key": "moving_dot"})
    component = CustomObjectComponent()
    mobj = component.build(
        spec,
        defaults=ComponentDefaults(font="Arial", text_font_size=36, bullet_font_size=32, formula_font_size=42),
    )

    before = float(mobj.submobjects[0].get_center()[0])
    mobj.composite_set_time(1.5)  # type: ignore[attr-defined]
    after = float(mobj.submobjects[0].get_center()[0])

    assert hasattr(mobj, "composite_set_time")
    assert hasattr(mobj, "composite_set_placement_absolute")
    assert after > before


def test_validate_plan_custom_object_params():
    plan_data = {
        "version": "0.1",
        "meta": {"name": "invalid_custom"},
        "objects": {
            "obj1": {
                "type": "CustomObject",
                "params": {
                    "spec": [],
                    "motion_span_s": "abc",
                },
            }
        },
        "scenes": [
            {
                "id": "s1",
                "layout": {
                    "type": "free",
                    "slots": {},
                    "params": {},
                    "placements": {
                        "obj1": {
                            "cx": 0.5,
                            "cy": 0.5,
                            "w": 0.5,
                            "h": 0.5,
                            "anchor": "C",
                        }
                    },
                },
                "actions": [
                    {"op": "wait", "duration": 0.2},
                ],
                "keep": [],
            }
        ],
    }

    plan = ScenePlan.model_validate(json.loads(json.dumps(plan_data)))
    errors = [item.message for item in validate_plan(plan)]

    assert any("CustomObject needs params.code_key" in msg for msg in errors)
    assert any("CustomObject params.spec must be an object" in msg for msg in errors)
    assert any("CustomObject params.motion_span_s must be a number" in msg for msg in errors)
