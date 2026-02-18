from __future__ import annotations

from pipeline.config import load_enums
from pipeline.run_llm2 import (
    _build_component_cards,
    _infer_domains,
    normalize_scene_draft_data,
    validate_scene_draft_data,
)


def _allowed_object_types() -> set[str]:
    enums = load_enums()
    return set(enums["object_types"])


def _valid_graph() -> dict:
    return {
        "version": "0.1",
        "space": {
            "x_range": [-10, 10],
            "y_range": [-6, 6],
            "unit": "scene_unit",
            "angle_unit": "deg",
            "origin": "center",
        },
        "parts": [
            {
                "id": "p_plane",
                "type": "Wall",
                "params": {"angle": 30, "length": 6.0},
                "style": {},
                "seed_pose": {"x": 0, "y": 0, "theta": 0, "scale": 1.0},
            },
            {
                "id": "p_block",
                "type": "Block",
                "params": {"width": 1.2, "height": 0.8},
                "style": {},
                "seed_pose": {"x": -1, "y": 1, "theta": 0, "scale": 1.0},
            },
        ],
        "tracks": [{"id": "t1", "type": "segment", "data": {"x1": -3, "y1": 1.2, "x2": 3, "y2": -0.5}}],
        "constraints": [{"id": "c1", "type": "on_track_pose", "args": {"part_id": "p_block", "track_id": "t1"}}],
        "motions": [],
    }


def _valid_draft() -> dict:
    return {
        "scenes": [
            {
                "id": "S1",
                "intent": "建图",
                "objects": [
                    {
                        "id": "o1",
                        "type": "TextBlock",
                        "params": {"text": "题意示意图"},
                        "style": {"size_level": "M"},
                        "priority": 1,
                    },
                    {
                        "id": "o2",
                        "type": "CompositeObject",
                        "params": {"graph": _valid_graph()},
                        "style": {"size_level": "XL"},
                        "priority": 1,
                    },
                ],
            }
        ]
    }


def test_validate_scene_draft_accepts_valid_composite():
    errors = validate_scene_draft_data(_valid_draft(), allowed_object_types=_allowed_object_types())
    assert errors == []


def test_validate_scene_draft_rejects_top_level_physics_object():
    data = _valid_draft()
    data["scenes"][0]["objects"].append(
        {
            "id": "o3",
            "type": "Block",
            "params": {"width": 1.0, "height": 0.6},
            "style": {},
            "priority": 2,
        }
    )
    errors = validate_scene_draft_data(data, allowed_object_types=_allowed_object_types())
    assert any("should be wrapped by CompositeObject" in e for e in errors)


def test_validate_scene_draft_rejects_missing_graph():
    data = _valid_draft()
    data["scenes"][0]["objects"][1]["params"] = {}
    errors = validate_scene_draft_data(data, allowed_object_types=_allowed_object_types())
    assert any("needs params.graph" in e for e in errors)


def test_validate_scene_draft_rejects_recursive_composite_part():
    data = _valid_draft()
    data["scenes"][0]["objects"][1]["params"]["graph"]["parts"][0]["type"] = "CompositeObject"
    errors = validate_scene_draft_data(data, allowed_object_types=_allowed_object_types())
    assert any(".type not allowed: CompositeObject" in e for e in errors)


def test_normalize_scene_draft_converts_formula_with_cjk_to_textblock():
    data = _valid_draft()
    data["scenes"][0]["objects"].append(
        {
            "id": "o3",
            "type": "Formula",
            "params": {"latex": "x=-1 处取极大值"},
            "style": {},
            "priority": 2,
        }
    )
    normalized, changed = normalize_scene_draft_data(data)
    assert changed
    assert normalized is not None
    obj = normalized["scenes"][0]["objects"][2]
    assert obj["type"] == "TextBlock"
    assert obj["params"] == {"text": "x=-1 处取极大值"}


def test_normalize_scene_draft_resets_non_center_origin():
    data = _valid_draft()
    data["scenes"][0]["objects"][1]["params"]["graph"]["space"]["origin"] = "custom"
    normalized, changed = normalize_scene_draft_data(data)
    assert changed
    assert normalized is not None
    assert normalized["scenes"][0]["objects"][1]["params"]["graph"]["space"]["origin"] == "center"


def test_validate_scene_draft_rejects_unbalanced_dollar_in_textblock():
    data = _valid_draft()
    data["scenes"][0]["objects"].append(
        {
            "id": "o3",
            "type": "TextBlock",
            "params": {"text": "速度为 $v=2 m/s"},
            "style": {},
            "priority": 2,
        }
    )
    errors = validate_scene_draft_data(data, allowed_object_types=_allowed_object_types())
    assert any("unbalanced $...$ delimiters" in e for e in errors)


def test_validate_scene_draft_rejects_latex_outside_dollar_in_textblock():
    data = _valid_draft()
    data["scenes"][0]["objects"].append(
        {
            "id": "o3",
            "type": "TextBlock",
            "params": {"text": "动能公式是 \\frac{1}{2}mv^2"},
            "style": {},
            "priority": 2,
        }
    )
    errors = validate_scene_draft_data(data, allowed_object_types=_allowed_object_types())
    assert any("LaTeX tokens outside $...$" in e for e in errors)


def test_validate_scene_draft_respects_formula_budget_max_4():
    data = _valid_draft()
    data["pedagogy_plan"] = {
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
    }
    for idx in range(5):
        data["scenes"][0]["objects"].append(
            {
                "id": f"o_formula_{idx}",
                "type": "Formula",
                "params": {"latex": f"x_{idx}=1"},
                "style": {},
                "priority": 2,
            }
        )
    errors = validate_scene_draft_data(data, allowed_object_types=_allowed_object_types())
    assert any("exceeds pedagogy budget max_new_formula=4" in e for e in errors)


def test_validate_scene_draft_requires_goal_when_need_single_goal_enabled():
    data = _valid_draft()
    data["pedagogy_plan"] = {
        "difficulty": "hard",
        "need_single_goal": True,
        "need_check_scene": False,
        "check_types": [],
        "cognitive_budget": {
            "max_visible_objects": 9,
            "max_new_formula": 4,
            "max_new_symbols": 10,
            "max_text_chars": 200,
        },
        "module_order": [],
    }
    errors = validate_scene_draft_data(data, allowed_object_types=_allowed_object_types())
    assert any(".goal required when pedagogy_plan.need_single_goal=true" in e for e in errors)


def test_validate_scene_draft_requires_check_scene_when_enabled():
    data = _valid_draft()
    data["pedagogy_plan"] = {
        "difficulty": "hard",
        "need_single_goal": False,
        "need_check_scene": True,
        "check_types": ["feasibility"],
        "cognitive_budget": {
            "max_visible_objects": 9,
            "max_new_formula": 4,
            "max_new_symbols": 10,
            "max_text_chars": 200,
        },
        "module_order": [],
    }
    errors = validate_scene_draft_data(data, allowed_object_types=_allowed_object_types())
    assert any("need_check_scene=true but no scene has is_check_scene=true" in e for e in errors)


def test_infer_domains_detects_mechanics_from_problem_text():
    domains = _infer_domains("斜面上滑块受摩擦后碰撞，求速度", "先用机械能守恒再用动量守恒")
    assert "mechanics" in domains


def test_build_component_cards_filters_by_domain():
    cards = _build_component_cards(["mechanics"])
    assert "Block" in cards
    assert "Ammeter" not in cards


def test_normalize_scene_draft_clamps_low_max_text_chars_to_60():
    data = _valid_draft()
    data["pedagogy_plan"] = {
        "difficulty": "medium",
        "need_single_goal": False,
        "need_check_scene": False,
        "check_types": [],
        "cognitive_budget": {
            "max_visible_objects": 5,
            "max_new_formula": 4,
            "max_new_symbols": 3,
            "max_text_chars": 20,
        },
        "module_order": [],
    }
    normalized, changed = normalize_scene_draft_data(data)
    assert changed
    assert normalized is not None
    assert normalized["pedagogy_plan"]["cognitive_budget"]["max_text_chars"] == 60


def test_normalize_scene_draft_trims_new_symbols_to_budget_limit():
    data = _valid_draft()
    data["pedagogy_plan"] = {
        "difficulty": "hard",
        "need_single_goal": False,
        "need_check_scene": False,
        "check_types": [],
        "cognitive_budget": {
            "max_visible_objects": 5,
            "max_new_formula": 4,
            "max_new_symbols": 3,
            "max_text_chars": 80,
        },
        "module_order": [],
    }
    data["scenes"][0]["new_symbols"] = ["a", "b", "c", "d", "e"]

    normalized, changed = normalize_scene_draft_data(data)
    assert changed
    assert normalized is not None
    assert normalized["scenes"][0]["new_symbols"] == ["a", "b", "c"]


def test_normalize_scene_draft_wraps_latex_tokens_inside_inline_math():
    data = _valid_draft()
    data["scenes"][0]["objects"].append(
        {
            "id": "o3",
            "type": "TextBlock",
            "params": {"text": "t=0.314\\text{s}时，P继续运动"},
            "style": {},
            "priority": 2,
        }
    )

    normalized, changed = normalize_scene_draft_data(data)
    assert changed
    assert normalized is not None
    fixed = normalized["scenes"][0]["objects"][2]["params"]["text"]
    assert "$" in fixed
    errors = validate_scene_draft_data(normalized, allowed_object_types=_allowed_object_types())
    assert not any("LaTeX tokens outside $...$" in e for e in errors)


def test_normalize_scene_draft_maps_role_aliases_to_allowed_roles():
    data = _valid_draft()
    data["scenes"][0]["roles"] = {
        "o1": "model",
        "o2": "equation",
    }

    normalized, changed = normalize_scene_draft_data(data)
    assert changed
    assert normalized is not None
    assert normalized["scenes"][0]["roles"]["o1"] == "support_eq"
    assert normalized["scenes"][0]["roles"]["o2"] == "core_eq"
    errors = validate_scene_draft_data(normalized, allowed_object_types=_allowed_object_types())
    assert not any("has unknown role" in e for e in errors)


def test_validate_scene_draft_requires_motion_for_dynamic_scene():
    data = _valid_draft()
    data["scenes"][0]["intent"] = "展示滑块运动过程"
    errors = validate_scene_draft_data(data, allowed_object_types=_allowed_object_types())
    assert any("params.graph.motions is required for dynamic scene" in e for e in errors)


def test_validate_scene_draft_rejects_discontinuous_on_track_schedule_segments():
    data = _valid_draft()
    data["scenes"][0]["intent"] = "展示滑块沿轨道运动"
    graph = data["scenes"][0]["objects"][1]["params"]["graph"]
    graph["tracks"].append({"id": "t2", "type": "segment", "data": {"x1": 3, "y1": -0.5, "x2": 5, "y2": -0.5}})
    graph["motions"] = [
        {
            "id": "m1",
            "type": "on_track_schedule",
            "args": {
                "part_id": "p_block",
                "anchor": "bottom_center",
                "segments": [
                    {"track_id": "t1", "u0": 0.0, "u1": 0.5, "s0": 0.0, "s1": 1.0},
                    {"track_id": "t2", "u0": 0.6, "u1": 1.0, "s0": 0.0, "s1": 1.0},
                ],
            },
            "timeline": [{"t": 0.0, "u": 0.0}, {"t": 2.0, "u": 1.0}],
        }
    ]
    errors = validate_scene_draft_data(data, allowed_object_types=_allowed_object_types())
    assert any("segments must be continuous in u" in e for e in errors)


def test_validate_scene_draft_accepts_continuous_on_track_schedule():
    data = _valid_draft()
    data["scenes"][0]["intent"] = "展示滑块沿轨道运动"
    graph = data["scenes"][0]["objects"][1]["params"]["graph"]
    graph["tracks"].append({"id": "t2", "type": "segment", "data": {"x1": 3, "y1": -0.5, "x2": 5, "y2": -0.5}})
    graph["motions"] = [
        {
            "id": "m1",
            "type": "on_track_schedule",
            "args": {
                "part_id": "p_block",
                "anchor": "bottom_center",
                "segments": [
                    {"track_id": "t1", "u0": 0.0, "u1": 0.5, "s0": 0.0, "s1": 1.0},
                    {"track_id": "t2", "u0": 0.5, "u1": 1.0, "s0": 0.0, "s1": 1.0},
                ],
            },
            "timeline": [{"t": 0.0, "u": 0.0}, {"t": 2.0, "u": 1.0}],
        }
    ]
    errors = validate_scene_draft_data(data, allowed_object_types=_allowed_object_types())
    assert not any("on_track_schedule" in e for e in errors)


def test_validate_scene_draft_reports_attach_using_track_id_with_clear_message():
    data = _valid_draft()
    graph = data["scenes"][0]["objects"][1]["params"]["graph"]
    graph["tracks"].append(
        {
            "id": "t_arc",
            "type": "arc",
            "data": {"center": {"x": 1.0, "y": 1.0}, "radius": 1.0, "start_angle": 180, "end_angle": 0},
        }
    )
    graph["constraints"].append(
        {
            "id": "c_attach_bad",
            "type": "attach",
            "args": {"part_a": "p_plane", "part_b": "t_arc"},
            "hard": True,
        }
    )
    errors = validate_scene_draft_data(data, allowed_object_types=_allowed_object_types())
    assert any("looks like a track id" in e for e in errors)


def test_normalize_scene_draft_auto_fixes_attach_track_ref_to_part_ref():
    data = _valid_draft()
    graph = data["scenes"][0]["objects"][1]["params"]["graph"]
    graph["parts"].append(
        {
            "id": "p_arc",
            "type": "ArcTrack",
            "params": {},
            "style": {},
            "seed_pose": {"x": 0, "y": 0, "theta": 0, "scale": 1.0},
        }
    )
    graph["tracks"].append(
        {
            "id": "t_arc",
            "type": "arc",
            "data": {"center": {"x": 1.0, "y": 1.0}, "radius": 1.0, "start_angle": 180, "end_angle": 0},
        }
    )
    graph["constraints"].append(
        {
            "id": "c_attach_bad",
            "type": "attach",
            "args": {"part_a": "p_plane", "part_b": "t_arc"},
            "hard": True,
        }
    )

    normalized, changed = normalize_scene_draft_data(data)
    assert changed
    assert normalized is not None
    fixed_graph = normalized["scenes"][0]["objects"][1]["params"]["graph"]
    fixed_constraint = [c for c in fixed_graph["constraints"] if c.get("id") == "c_attach_bad"][0]
    assert fixed_constraint["args"]["part_b"] == "p_arc"


def test_normalize_scene_draft_can_create_arc_part_from_arc_track_for_attach():
    data = _valid_draft()
    graph = data["scenes"][0]["objects"][1]["params"]["graph"]
    graph["tracks"].append(
        {
            "id": "t_arc",
            "type": "arc",
            "data": {"center": {"x": 2.0, "y": 1.0}, "radius": 1.5, "start_angle": 180, "end_angle": 0},
        }
    )
    graph["constraints"].append(
        {
            "id": "c_attach_bad",
            "type": "attach",
            "args": {"part_a": "p_plane", "part_b": "t_arc"},
            "hard": True,
        }
    )

    normalized, changed = normalize_scene_draft_data(data)
    assert changed
    assert normalized is not None
    fixed_graph = normalized["scenes"][0]["objects"][1]["params"]["graph"]
    part_ids = {part["id"] for part in fixed_graph["parts"]}
    assert "p_arc" in part_ids
    fixed_constraint = [c for c in fixed_graph["constraints"] if c.get("id") == "c_attach_bad"][0]
    assert fixed_constraint["args"]["part_b"] == "p_arc"
    errors = validate_scene_draft_data(normalized, allowed_object_types=_allowed_object_types())
    assert not any("looks like a track id" in e for e in errors)


def test_validate_scene_draft_allows_bbox_anchors_like_right_center():
    data = _valid_draft()
    graph = data["scenes"][0]["objects"][1]["params"]["graph"]
    graph["parts"].append(
        {
            "id": "p_flat",
            "type": "Wall",
            "params": {"angle": 0, "length": 2.0},
            "style": {},
            "seed_pose": {"x": 1.0, "y": 0.0, "theta": 0, "scale": 1.0},
        }
    )
    graph["constraints"].append(
        {
            "id": "c_attach_bbox_anchor",
            "type": "attach",
            "args": {
                "part_a": "p_plane",
                "anchor_a": "right_center",
                "part_b": "p_flat",
                "anchor_b": "left_center",
            },
            "hard": True,
        }
    )
    errors = validate_scene_draft_data(data, allowed_object_types=_allowed_object_types())
    assert not any("c_attach_bbox_anchor" in e and "invalid for part" in e for e in errors)
