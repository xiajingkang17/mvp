from __future__ import annotations

import pytest

pytest.importorskip("manim")
from manim import VGroup

from components.base import ComponentDefaults
from components.composite.object_component import CompositeObjectComponent
from render.registry import DEFAULT_REGISTRY
from schema.scene_plan_models import ObjectSpec


def _defaults() -> ComponentDefaults:
    return ComponentDefaults(
        font="Arial",
        text_font_size=36,
        bullet_font_size=34,
        formula_font_size=48,
    )


def _graph(parts: list[dict]) -> dict:
    return {
        "version": "0.1",
        "space": {
            "x_range": [-10, 10],
            "y_range": [-6, 6],
            "unit": "scene_unit",
            "angle_unit": "deg",
            "origin": "center",
        },
        "parts": parts,
        "tracks": [],
        "constraints": [],
        "motions": [],
    }


def _composite_spec(graph: dict) -> ObjectSpec:
    return ObjectSpec(
        type="CompositeObject",
        params={"graph": graph},
        style={},
        priority=1,
    )


def test_registry_contains_composite_object_component():
    assert "CompositeObject" in DEFAULT_REGISTRY.components


def test_composite_component_builds_vgroup_from_graph_parts():
    component = CompositeObjectComponent()
    graph = _graph(
        [
            {
                "id": "p1",
                "type": "Block",
                "params": {"width": 1.2, "height": 0.8},
                "style": {},
                "seed_pose": {"x": 2.0, "y": -1.0, "theta": 15.0, "scale": 1.0},
            },
            {
                "id": "p2",
                "type": "Wall",
                "params": {"length": 1.8, "angle": 90.0},
                "style": {},
                "seed_pose": {"x": -1.5, "y": 1.25, "theta": 0.0, "scale": 1.0},
            },
        ]
    )

    mobj = component.build(_composite_spec(graph), defaults=_defaults())

    assert isinstance(mobj, VGroup)
    assert len(mobj.submobjects) == 2
    assert mobj.submobjects[0].get_center()[0] == pytest.approx(2.0, abs=1e-6)
    assert mobj.submobjects[0].get_center()[1] == pytest.approx(-1.0, abs=1e-6)
    assert mobj.submobjects[1].get_center()[0] == pytest.approx(-1.5, abs=1e-6)
    assert mobj.submobjects[1].get_center()[1] == pytest.approx(1.25, abs=1e-6)


def test_composite_component_rejects_recursive_part_type():
    component = CompositeObjectComponent()
    graph = _graph(
        [
            {
                "id": "p_recursive",
                "type": "CompositeObject",
                "params": {},
                "style": {},
                "seed_pose": {"x": 0.0, "y": 0.0, "theta": 0.0, "scale": 1.0},
            }
        ]
    )

    with pytest.raises(ValueError, match="cannot recursively contain"):
        component.build(_composite_spec(graph), defaults=_defaults())


def test_composite_component_runtime_time_and_placement_updates():
    component = CompositeObjectComponent()
    graph = _graph(
        [
            {
                "id": "p1",
                "type": "Block",
                "params": {"width": 2.0, "height": 2.0},
                "style": {},
                "seed_pose": {"x": 0.0, "y": 0.0, "theta": 0.0, "scale": 1.0},
            }
        ]
    )
    graph["tracks"] = [{"id": "t1", "type": "segment", "data": {"x1": 0.0, "y1": 0.0, "x2": 10.0, "y2": 0.0}}]
    graph["motions"] = [
        {
            "id": "m1",
            "type": "on_track",
            "args": {"part_id": "p1", "track_id": "t1", "anchor": "bottom_center"},
            "timeline": [{"t": 0.0, "s": 0.0}, {"t": 1.0, "s": 1.0}],
        }
    ]
    spec = _composite_spec(graph)
    spec.params["motion_time"] = 0.0

    group = component.build(spec, defaults=_defaults())
    assert callable(getattr(group, "composite_set_time", None))
    assert callable(getattr(group, "composite_set_placement", None))

    group.composite_set_time(1.0)
    moved_center = group.submobjects[0].get_center()
    assert moved_center[0] == pytest.approx(10.0, abs=1e-6)
    assert moved_center[1] == pytest.approx(1.0, abs=1e-6)

    group.composite_set_placement(0.5, 2.0, -1.0)
    placed_center = group.submobjects[0].get_center()
    assert placed_center[0] == pytest.approx(7.0, abs=1e-6)
    assert placed_center[1] == pytest.approx(-0.5, abs=1e-6)
