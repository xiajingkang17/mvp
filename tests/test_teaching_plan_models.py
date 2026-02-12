from __future__ import annotations

import pytest

from schema.teaching_plan_models import TeachingPlan


def _valid_plan() -> dict:
    return {
        "explanation_full": "完整解题过程",
        "global_symbols": [{"name": "m", "meaning": "质量", "unit": "kg"}],
        "sub_questions": [
            {
                "id": "Q1",
                "question": "求v",
                "goal": "求速度v",
                "device_scene_needed": True,
                "variable_annotations": ["m", "mu", "theta"],
                "given_conditions": ["AB光滑", "BC粗糙"],
                "method_choice": {"method": "energy", "reason": "可直接列能量方程"},
                "derivation_steps": [
                    {"type": "equation", "content": "mgh-fL=1/2mv^2"},
                    {"type": "compute", "content": "代入数值"},
                ],
                "result": {"expression": "v=6.0", "unit": "m/s"},
                "sanity_checks": ["单位合理"],
                "scene_packets": [
                    {"content_items": ["diagram", "goal", "knowns"], "primary_item": "diagram"},
                    {"content_items": ["core_equation", "derive_step"], "primary_item": "core_equation"},
                ],
            }
        ],
    }


def test_teaching_plan_model_accepts_valid_payload():
    model = TeachingPlan.model_validate(_valid_plan())
    assert model.sub_questions[0].scene_packets[0].primary_item == "diagram"


def test_teaching_plan_model_rejects_primary_not_in_content_items():
    data = _valid_plan()
    data["sub_questions"][0]["scene_packets"][0] = {
        "content_items": ["diagram", "goal"],
        "primary_item": "core_equation",
    }
    with pytest.raises(Exception):  # noqa: B017
        TeachingPlan.model_validate(data)

