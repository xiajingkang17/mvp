from __future__ import annotations

from types import SimpleNamespace

from layout.engine import Frame, SafeArea
from layout.refine_params import refine_layout_params
from schema.scene_plan_models import ObjectSpec


def test_refine_params_preserves_slot_scales():
    object_specs = {
        "o1": ObjectSpec(type="TextBlock", params={"text": "A"}, style={"size_level": "M"}, priority=3),
        "o2": ObjectSpec(type="TextBlock", params={"text": "B"}, style={"size_level": "M"}, priority=3),
    }
    objects = {
        "o1": SimpleNamespace(width=2.0, height=1.0),
        "o2": SimpleNamespace(width=2.0, height=1.0),
    }
    slots = {"left": "o1", "right": "o2"}

    refined = refine_layout_params(
        "left_right",
        slots,
        llm_params={"slot_scales": {"left": {"w": 0.6, "h": 0.7}}},
        object_specs=object_specs,
        objects=objects,
        base_sizes=None,
        safe_area=SafeArea(left=0.05, right=0.05, top=0.05, bottom=0.05),
        frame=Frame(width=14.222, height=8.0),
        max_adjust=0.2,
        min_slot_w_norm=0.05,
        min_slot_h_norm=0.05,
        enabled=True,
    )

    assert refined == {"slot_scales": {"left": {"w": 0.6, "h": 0.7}}}


def test_refine_params_fallback_to_default_when_slot_scale_too_small():
    object_specs = {
        "o1": ObjectSpec(type="TextBlock", params={"text": "A"}, style={"size_level": "M"}, priority=3),
        "o2": ObjectSpec(type="TextBlock", params={"text": "B"}, style={"size_level": "M"}, priority=3),
    }
    objects = {
        "o1": SimpleNamespace(width=2.0, height=1.0),
        "o2": SimpleNamespace(width=2.0, height=1.0),
    }
    slots = {"left": "o1", "right": "o2"}

    refined = refine_layout_params(
        "left_right",
        slots,
        llm_params={"slot_scales": {"left": {"w": 0.2, "h": 0.2}}},
        object_specs=object_specs,
        objects=objects,
        base_sizes=None,
        safe_area=SafeArea(left=0.05, right=0.05, top=0.05, bottom=0.05),
        frame=Frame(width=14.222, height=8.0),
        max_adjust=0.2,
        min_slot_w_norm=0.2,
        min_slot_h_norm=0.2,
        enabled=True,
    )

    assert refined == {}
