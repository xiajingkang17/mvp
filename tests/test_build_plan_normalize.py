from __future__ import annotations

from pipeline.build_plan import (
    _normalize_actions,
    _canonicalize_layout_slots,
    _normalize_draft_object,
    _normalize_layout_slots,
    _normalize_roles,
    _normalize_str_list,
)


def test_normalize_formula_with_cjk_to_textblock():
    object_type, params = _normalize_draft_object(
        {"type": "Formula", "params": {"latex": "x = -1 \u5904\u53d6\u6781\u5927\u503c"}}
    )
    assert object_type == "TextBlock"
    assert params == {"text": "x = -1 \u5904\u53d6\u6781\u5927\u503c"}


def test_normalize_textblock_content_to_text():
    object_type, params = _normalize_draft_object({"type": "TextBlock", "params": {"content": "abc"}})
    assert object_type == "TextBlock"
    assert params == {"text": "abc"}


def test_normalize_layout_slots_filters_none_values():
    slots = _normalize_layout_slots({"left": "o1", "side": None, "count": 2, "  ": "x"})
    assert slots == {"left": "o1", "count": "2"}


def test_canonicalize_layout_slots_accepts_left_right_aliases():
    slots = _canonicalize_layout_slots(
        "left4_right4",
        {"left_1": "o1", "right-2": "o2", "left3": "o3"},
    )
    assert slots == {"left1": "o1", "right2": "o2", "left3": "o3"}


def test_canonicalize_layout_slots_accepts_grid_aliases():
    slots = _canonicalize_layout_slots(
        "grid_3x3",
        {"c1": "o1", "c3": "o3", "r2c2": "o5"},
    )
    assert slots == {"a": "o1", "c": "o3", "e": "o5"}


def test_normalize_roles_filters_empty_pairs():
    roles = _normalize_roles({" o1 ": " diagram ", "": "core_eq", "o2": ""})
    assert roles == {"o1": "diagram"}


def test_normalize_str_list_filters_empty_values():
    values = _normalize_str_list([" a ", "", "  ", 1, None])
    assert values == ["a", "1"]


def test_normalize_actions_accepts_legacy_target_field():
    actions = _normalize_actions(
        [
            {"op": "play", "anim": "fade_in", "target": "o1"},
            {"op": "wait", "duration": 0.5},
        ]
    )
    assert actions[0]["targets"] == ["o1"]
    assert "target" not in actions[0]
    assert actions[1] == {"op": "wait", "duration": 0.5}
