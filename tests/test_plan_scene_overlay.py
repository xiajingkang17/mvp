from __future__ import annotations

from types import SimpleNamespace

import pytest

pytest.importorskip("manim")

from layout.engine import Frame, SafeArea
from render.plan_scene import (
    _build_auto_stack_placements,
    _collect_scene_object_ids,
    _ordered_unslotted_object_ids,
)


def _scene_like():
    actions = [
        SimpleNamespace(targets=["o_text"], src=None, dst=None),
        SimpleNamespace(targets=["o_formula"], src=None, dst=None),
        SimpleNamespace(targets=["o_result"], src=None, dst=None),
    ]
    layout = SimpleNamespace(type="left_right", slots={"left": "o_diagram", "right": "o_text"}, params={})
    return SimpleNamespace(layout=layout, actions=actions, keep=["o_diagram", "o_text", "o_formula", "o_result"])


def test_collect_scene_object_ids_includes_slots_actions_keep():
    scene = _scene_like()
    ids = _collect_scene_object_ids(scene)
    assert ids == {"o_diagram", "o_text", "o_formula", "o_result"}


def test_unslotted_order_follows_action_order():
    scene = _scene_like()
    referenced = _collect_scene_object_ids(scene)
    unslotted = _ordered_unslotted_object_ids(scene, referenced=referenced)
    assert unslotted == ["o_formula", "o_result"]


def test_auto_stack_reuses_right_slot_for_all_right_content():
    scene = _scene_like()
    placements = _build_auto_stack_placements(
        scene,
        referenced=_collect_scene_object_ids(scene),
        safe_area=SafeArea(left=0.05, right=0.05, top=0.05, bottom=0.05),
        frame=Frame(width=14.222, height=8.0),
        params={},
    )

    # right slot object should be restacked with additional right-side objects
    assert set(placements.keys()) == {"o_text", "o_formula", "o_result"}
    ys = [placements["o_text"].center_y, placements["o_formula"].center_y, placements["o_result"].center_y]
    assert ys[0] > ys[1] > ys[2]
    assert placements["o_text"].slot_id.startswith("auto:right:")
