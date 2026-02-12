from __future__ import annotations

import pytest

pytest.importorskip("manim")

from components.physics.object_components import build_physics_components
from components.physics.specs import PHYSICS_OBJECT_PARAM_SPECS
from pipeline.config import load_enums


def test_physics_component_types_are_in_enums():
    physics_types = set(build_physics_components().keys())
    enum_types = set(load_enums()["object_types"])
    assert physics_types.issubset(enum_types)


def test_physics_component_specs_cover_registered_types():
    physics_types = set(build_physics_components().keys())
    spec_types = set(PHYSICS_OBJECT_PARAM_SPECS.keys())
    assert physics_types.issubset(spec_types)
