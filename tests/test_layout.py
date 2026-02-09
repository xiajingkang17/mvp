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

