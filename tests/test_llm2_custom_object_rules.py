from __future__ import annotations

import json

from pipeline.run_llm2 import _parse_and_validate


def _build_min_scene_with_object(obj: dict) -> dict:
    return {
        "version": "0.1",
        "scenes": [
            {
                "id": "s1",
                "objects": [obj],
                "narrative_storyboard": {
                    "intro": "introduce object",
                    "key_formulae": [],
                    "animation_steps": [
                        {
                            "id": "step_1",
                            "description": "show object",
                            "targets": [obj["id"]],
                            "duration_s": 1.0,
                        }
                    ],
                    "bridge_to_next": "",
                },
            }
        ],
    }


def test_llm2_custom_object_valid_hints_passes():
    obj = {
        "id": "co_1",
        "type": "CustomObject",
        "params": {
            "custom_role": "special_motion",
            "draw_prompt": "draw a ribbon-like curve with markers",
            "motion_prompt": "marker moves along curve and deforms",
            "codegen_request": {
                "enabled": True,
                "scope": "motion",
                "intent": "需要由 llm_codegen 生成连续轨迹运动",
                "kind_hint": "special_motion",
            },
            "manim_api_hints": ["ValueTracker", "always_redraw"],
            "motion_span_s_hint": 6.0,
        },
        "style": {},
    }
    payload = _build_min_scene_with_object(obj)
    data, errors = _parse_and_validate(json.dumps(payload, ensure_ascii=False))
    assert data is not None
    assert errors == []


def test_llm2_custom_object_missing_prompts_fails():
    obj = {
        "id": "co_1",
        "type": "CustomObject",
        "params": {
            "custom_role": "new_component",
        },
        "style": {},
    }
    payload = _build_min_scene_with_object(obj)
    data, errors = _parse_and_validate(json.dumps(payload, ensure_ascii=False))
    assert data is None
    assert any("params.draw_prompt" in msg for msg in errors)
    assert any("params.motion_prompt" in msg for msg in errors)
    assert any("params.codegen_request" in msg for msg in errors)


def test_llm2_custom_object_invalid_role_fails():
    obj = {
        "id": "co_1",
        "type": "CustomObject",
        "params": {
            "custom_role": "unknown_role",
            "draw_prompt": "draw shape",
            "motion_prompt": "move shape",
        },
        "style": {},
    }
    payload = _build_min_scene_with_object(obj)
    data, errors = _parse_and_validate(json.dumps(payload, ensure_ascii=False))
    assert data is None
    assert any("params.custom_role='unknown_role' invalid" in msg for msg in errors)
