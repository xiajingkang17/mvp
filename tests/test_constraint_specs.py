from __future__ import annotations

from llm_constraints.constraints_spec import validate_constraint_args


def test_on_track_pose_valid_args():
    errors = validate_constraint_args(
        "on_track_pose",
        {
            "part_id": "p_block",
            "track_id": "t_slope",
            "anchor": "bottom_center",
            "s": 0.25,
            "angle_mode": "tangent",
            "contact_side": "outer",
        },
    )
    assert errors == []


def test_on_track_pose_rejects_unknown_arg():
    errors = validate_constraint_args(
        "on_track_pose",
        {"part_id": "p1", "track_id": "t1", "foo": 1},
    )
    assert any("unknown args" in item for item in errors)


def test_on_track_pose_rejects_removed_offset_args():
    errors_normal = validate_constraint_args(
        "on_track_pose",
        {"part_id": "p1", "track_id": "t1", "normal_offset": 0.2},
    )
    errors_auto = validate_constraint_args(
        "on_track_pose",
        {"part_id": "p1", "track_id": "t1", "auto_clearance": True},
    )
    assert any("unknown args" in item for item in errors_normal)
    assert any("unknown args" in item for item in errors_auto)


def test_attach_accepts_aliases():
    errors = validate_constraint_args(
        "attach",
        {
            "from_part_id": "p1",
            "to_part_id": "p2",
            "from_anchor": "right_center",
            "to_anchor": "left_center",
            "mode": "a_to_b",
        },
    )
    assert errors == []


def test_attach_accepts_rigid_flag():
    errors = validate_constraint_args(
        "attach",
        {
            "part_a": "p1",
            "anchor_a": "end",
            "part_b": "p2",
            "anchor_b": "start",
            "mode": "b_to_a",
            "rigid": True,
        },
    )
    assert errors == []


def test_align_constraints_are_unsupported():
    errors_angle = validate_constraint_args("align_angle", {"part_id": "p1"})
    errors_axis = validate_constraint_args("align_axis", {"part_a": "p1", "part_b": "p2"})
    assert errors_angle == ["unsupported constraint type: align_angle"]
    assert errors_axis == ["unsupported constraint type: align_axis"]


def test_unknown_constraint_type():
    errors = validate_constraint_args("not_exists", {"part_id": "p1"})
    assert errors == ["unsupported constraint type: not_exists"]
