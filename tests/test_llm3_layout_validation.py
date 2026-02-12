from __future__ import annotations

from pipeline.config import load_enums
from pipeline.run_llm3 import _validate_layout_data


def _draft() -> dict:
    return {
        "scenes": [
            {
                "id": "S1",
                "objects": [
                    {"id": "o_diagram", "type": "CompositeObject", "params": {}, "style": {}, "priority": 1},
                    {"id": "o_eq_1", "type": "Formula", "params": {"latex": "x=1"}, "style": {}, "priority": 1},
                    {"id": "o_eq_2", "type": "Formula", "params": {"latex": "x=2"}, "style": {}, "priority": 1},
                    {"id": "o_unused", "type": "TextBlock", "params": {"text": "unused"}, "style": {}, "priority": 1},
                ],
            }
        ]
    }


def _valid_layout() -> dict:
    return {
        "scenes": [
            {
                "id": "S1",
                "layout": {
                    "type": "left_right",
                    "slots": {"left": "o_diagram", "right": "o_eq_1"},
                    "params": {"slot_scales": {"left": {"w": 0.9, "h": 0.8}}},
                },
                "actions": [
                    {"op": "play", "anim": "fade_in", "targets": ["o_diagram"]},
                    {"op": "play", "anim": "transform", "targets": ["o_eq_1", "o_eq_2"]},
                ],
                "keep": ["o_diagram", "o_eq_2"],
                "roles": {"o_diagram": "diagram", "o_eq_2": "core_eq"},
            }
        ]
    }


def test_validate_layout_data_accepts_valid_contract():
    errors = _validate_layout_data(data=_valid_layout(), draft=_draft(), enums=load_enums())
    assert errors == []


def test_validate_layout_data_rejects_transform_with_single_target():
    data = _valid_layout()
    data["scenes"][0]["actions"][1] = {"op": "play", "anim": "transform", "targets": ["o_eq_1"]}
    errors = _validate_layout_data(data=data, draft=_draft(), enums=load_enums())
    assert any("transform requires src+dst" in e for e in errors)


def test_validate_layout_data_rejects_roles_object_not_used():
    data = _valid_layout()
    data["scenes"][0]["roles"]["o_unused"] = "support_eq"
    errors = _validate_layout_data(data=data, draft=_draft(), enums=load_enums())
    assert any("roles references object not used in this scene: o_unused" in e for e in errors)
