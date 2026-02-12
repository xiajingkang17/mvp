from __future__ import annotations

from layout.params import default_params, sanitize_params


def test_default_params_are_empty_for_all_layout_templates():
    assert default_params("hero_side") == {}
    assert default_params("left_right") == {}
    assert default_params("left3_right3") == {}
    assert default_params("left4_right4") == {}
    assert default_params("grid_2x2") == {}
    assert default_params("grid_3x3") == {}


def test_sanitize_params_only_keeps_slot_scales():
    cleaned = sanitize_params(
        "left_right",
        {
            "left_ratio": 0.6,
            "row_weights": [3, 1],
            "slot_scales": {
                "left": {"w": 0.4, "h": 0.8},
                "right": {"width": 0.3, "height": 0.7},
            },
        },
    )
    assert cleaned == {
        "slot_scales": {
            "left": {"w": 0.4, "h": 0.8},
            "right": {"w": 0.3, "h": 0.7},
        },
    }
