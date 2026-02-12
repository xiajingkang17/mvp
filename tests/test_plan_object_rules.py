from __future__ import annotations

from pipeline.validate_plan import autofix_plan, validate_plan
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


def test_validate_rejects_formula_with_cjk_latex():
    plan = _make_plan_with_object(
        {
            "type": "Formula",
            "params": {"latex": "x = -1 \u5904\u53d6\u6781\u5927\u503c"},
            "style": {},
            "priority": 1,
        }
    )
    errors = validate_plan(plan)
    assert any("contains CJK characters" in e.message for e in errors)


def test_autofix_converts_formula_with_cjk_to_textblock():
    latex = "x = -1 \u5904\u53d6\u6781\u5927\u503c"
    plan = _make_plan_with_object(
        {
            "type": "Formula",
            "params": {"latex": latex},
            "style": {},
            "priority": 1,
        }
    )

    changed = autofix_plan(plan)

    assert changed
    assert plan.objects["o1"].type == "TextBlock"
    assert plan.objects["o1"].params == {"text": latex}
    assert validate_plan(plan) == []


def test_autofix_normalizes_textblock_content_field():
    plan = _make_plan_with_object(
        {
            "type": "TextBlock",
            "params": {"content": "hello"},
            "style": {},
            "priority": 1,
        }
    )

    changed = autofix_plan(plan)

    assert changed
    assert plan.objects["o1"].params == {"text": "hello"}
    assert validate_plan(plan) == []


def test_validate_rejects_textblock_with_unbalanced_dollar():
    plan = _make_plan_with_object(
        {
            "type": "TextBlock",
            "params": {"text": "速度为 $v=2 m/s"},
            "style": {},
            "priority": 1,
        }
    )
    errors = validate_plan(plan)
    assert any("unbalanced $...$ delimiters" in e.message for e in errors)


def test_validate_rejects_textblock_with_latex_outside_dollar():
    plan = _make_plan_with_object(
        {
            "type": "TextBlock",
            "params": {"text": "动能公式是 \\frac{1}{2}mv^2"},
            "style": {},
            "priority": 1,
        }
    )
    errors = validate_plan(plan)
    assert any("LaTeX tokens outside $...$" in e.message for e in errors)


def test_validate_respects_scene_formula_budget_max_4():
    objects = {}
    slots = {}
    for idx in range(5):
        oid = f"f{idx}"
        objects[oid] = {"type": "Formula", "params": {"latex": f"x_{idx}=1"}, "style": {}, "priority": 1}
        slots[f"left{idx + 1}" if idx < 3 else f"right{idx - 2}"] = oid

    raw = {
        "version": "0.1",
        "meta": {},
        "pedagogy_plan": {
            "difficulty": "medium",
            "need_single_goal": False,
            "need_check_scene": False,
            "check_types": [],
            "cognitive_budget": {
                "max_visible_objects": 9,
                "max_new_formula": 4,
                "max_new_symbols": 10,
                "max_text_chars": 200,
            },
            "module_order": [],
        },
        "objects": objects,
        "scenes": [
            {
                "id": "S1",
                "goal": "推导",
                "layout": {"type": "left3_right3", "slots": slots, "params": {}},
                "actions": [],
                "keep": list(objects.keys()),
            }
        ],
    }
    plan = ScenePlan.model_validate(raw)
    errors = validate_plan(plan)
    assert any("exceeds pedagogy budget max_new_formula=4" in e.message for e in errors)


def test_validate_requires_check_scene_when_pedagogy_demands_it():
    raw = {
        "version": "0.1",
        "meta": {},
        "pedagogy_plan": {
            "difficulty": "hard",
            "need_single_goal": False,
            "need_check_scene": True,
            "check_types": ["feasibility"],
            "cognitive_budget": {
                "max_visible_objects": 4,
                "max_new_formula": 4,
                "max_new_symbols": 3,
                "max_text_chars": 38,
            },
            "module_order": [],
        },
        "objects": {
            "o1": {"type": "TextBlock", "params": {"text": "结论"}, "style": {}, "priority": 1}
        },
        "scenes": [
            {
                "id": "S1",
                "layout": {"type": "hero_side", "slots": {"hero": "o1"}, "params": {}},
                "actions": [],
                "keep": ["o1"],
            }
        ],
    }
    plan = ScenePlan.model_validate(raw)
    errors = validate_plan(plan)
    assert any("need_check_scene=true but no scene has is_check_scene=true" in e.message for e in errors)
