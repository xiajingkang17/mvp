from __future__ import annotations

from layout.engine import Frame, SafeArea, compute_placements


def test_compute_placements_within_frame():
    safe = SafeArea(left=0.05, right=0.05, top=0.05, bottom=0.05)
    frame = Frame(width=14.222, height=8.0)
    placements = compute_placements(
        "grid_2x2",
        {"a": "o1", "b": "o2", "c": "o3", "d": "o4"},
        safe_area=safe,
        frame=frame,
    )
    for placement in placements.values():
        assert abs(placement.center_x) <= frame.width / 2
        assert abs(placement.center_y) <= frame.height / 2
        assert placement.width > 0
        assert placement.height > 0


def test_compute_placements_left4_right4():
    safe = SafeArea(left=0.05, right=0.05, top=0.05, bottom=0.05)
    frame = Frame(width=14.222, height=8.0)
    placements = compute_placements(
        "left4_right4",
        {
            "left1": "o1",
            "right1": "o2",
            "left2": "o3",
            "right2": "o4",
            "left3": "o5",
            "right3": "o6",
            "left4": "o7",
            "right4": "o8",
        },
        safe_area=safe,
        frame=frame,
    )
    assert len(placements) == 8


def test_compute_placements_left3_right3():
    safe = SafeArea(left=0.05, right=0.05, top=0.05, bottom=0.05)
    frame = Frame(width=14.222, height=8.0)
    placements = compute_placements(
        "left3_right3",
        {
            "left1": "o1",
            "right1": "o2",
            "left2": "o3",
            "right2": "o4",
            "left3": "o5",
            "right3": "o6",
        },
        safe_area=safe,
        frame=frame,
    )
    assert len(placements) == 6


def test_compute_placements_grid_2x2_ignores_template_level_weights():
    safe = SafeArea(left=0.0, right=0.0, top=0.0, bottom=0.0)
    frame = Frame(width=10.0, height=6.0)
    base = compute_placements(
        "grid_2x2",
        {"a": "o1", "b": "o2", "c": "o3", "d": "o4"},
        safe_area=safe,
        frame=frame,
    )
    with_unused_params = compute_placements(
        "grid_2x2",
        {"a": "o1", "b": "o2", "c": "o3", "d": "o4"},
        safe_area=safe,
        frame=frame,
        params={"col_weights": [0.7, 0.3], "row_weights": [0.6, 0.4]},
    )

    assert with_unused_params["o1"].width == base["o1"].width
    assert with_unused_params["o2"].width == base["o2"].width
    assert with_unused_params["o1"].height == base["o1"].height
    assert with_unused_params["o3"].height == base["o3"].height


def test_compute_placements_slot_scales_override_single_slot_size():
    safe = SafeArea(left=0.0, right=0.0, top=0.0, bottom=0.0)
    frame = Frame(width=10.0, height=6.0)

    base = compute_placements(
        "left_right",
        {"left": "o1", "right": "o2"},
        safe_area=safe,
        frame=frame,
        params={},
    )
    scaled = compute_placements(
        "left_right",
        {"left": "o1", "right": "o2"},
        safe_area=safe,
        frame=frame,
        params={"slot_scales": {"left": {"w": 0.6, "h": 0.5}}},
    )

    assert scaled["o1"].width < base["o1"].width
    assert scaled["o1"].height < base["o1"].height
    assert scaled["o2"].width == base["o2"].width
    assert scaled["o2"].height == base["o2"].height

