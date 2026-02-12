from __future__ import annotations

import itertools
import math

import pytest

pytest.importorskip("manim")

from components.base import ComponentDefaults
from components.composite.object_component import CompositeObjectComponent
from layout.engine import Placement
from render.plan_scene import apply_placement
from schema.scene_plan_models import ObjectSpec


def _defaults() -> ComponentDefaults:
    return ComponentDefaults(
        font="Arial",
        text_font_size=36,
        bullet_font_size=34,
        formula_font_size=48,
    )


def _pairwise_distances(points: list[tuple[float, float]]) -> list[float]:
    values: list[float] = []
    for (x1, y1), (x2, y2) in itertools.combinations(points, 2):
        values.append(math.hypot(x1 - x2, y1 - y2))
    return values


def _ratios(values: list[float], base: list[float]) -> list[float]:
    out: list[float] = []
    for v, b in zip(values, base, strict=True):
        out.append(v / b if b > 1e-9 else 1.0)
    return out


def _assert_uniform_scale(ratios: list[float], tol: float = 1e-6) -> None:
    first = ratios[0]
    for r in ratios[1:]:
        assert r == pytest.approx(first, abs=tol)


def _make_composite() -> object:
    component = CompositeObjectComponent()
    graph = {
        "version": "0.1",
        "space": {"x_range": [-10, 10], "y_range": [-6, 6], "unit": "scene_unit", "angle_unit": "deg", "origin": "center"},
        "parts": [
            {"id": "p1", "type": "Block", "params": {"width": 1.0, "height": 0.8}, "style": {}, "seed_pose": {"x": 0.0, "y": 0.0, "theta": 0.0, "scale": 1.0}},
            {"id": "p2", "type": "Block", "params": {"width": 1.0, "height": 0.8}, "style": {}, "seed_pose": {"x": 4.0, "y": 0.0, "theta": 0.0, "scale": 1.0}},
            {"id": "p3", "type": "Block", "params": {"width": 1.0, "height": 0.8}, "style": {}, "seed_pose": {"x": 1.0, "y": 3.0, "theta": 0.0, "scale": 1.0}},
        ],
        "tracks": [],
        "constraints": [],
        "motions": [],
    }
    spec = ObjectSpec(type="CompositeObject", params={"graph": graph}, style={}, priority=1)
    return component.build(spec, defaults=_defaults())


def test_composite_slot_fit_preserves_internal_geometry_across_placements():
    group = _make_composite()

    def _centers():
        return [(float(m.get_center()[0]), float(m.get_center()[1])) for m in group.submobjects]

    base_points = _centers()
    base_dist = _pairwise_distances(base_points)

    placement1 = Placement(object_id="o", slot_id="hero", center_x=0.0, center_y=0.0, width=8.0, height=4.0, anchor="C")
    apply_placement(group, placement1, slot_padding=0.05)
    after1_points = _centers()
    ratios1 = _ratios(_pairwise_distances(after1_points), base_dist)
    _assert_uniform_scale(ratios1)
    assert float(group.get_center()[0]) == pytest.approx(0.0, abs=1e-6)
    assert float(group.get_center()[1]) == pytest.approx(0.0, abs=1e-6)

    placement2 = Placement(object_id="o", slot_id="right", center_x=2.0, center_y=-1.0, width=4.0, height=2.0, anchor="C")
    apply_placement(group, placement2, slot_padding=0.05)
    after2_points = _centers()
    ratios2 = _ratios(_pairwise_distances(after2_points), base_dist)
    _assert_uniform_scale(ratios2)
    assert float(group.get_center()[0]) == pytest.approx(2.0, abs=1e-6)
    assert float(group.get_center()[1]) == pytest.approx(-1.0, abs=1e-6)
