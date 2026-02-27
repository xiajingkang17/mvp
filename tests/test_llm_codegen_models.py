from __future__ import annotations

import pytest

from schema.scene_codegen_models import SceneCodegenPlan


def test_scene_codegen_model_accepts_valid_payload():
    payload = {
        "version": "0.1",
        "objects": [
            {
                "object_id": "orbit_demo",
                "code_key": "orbit_probe",
                "spec": {"radius": 1.2, "omega": 2.0},
                "motion_span_s": 4.0,
            }
        ],
    }
    model = SceneCodegenPlan.model_validate(payload)
    assert model.objects[0].object_id == "orbit_demo"
    assert model.objects[0].code_key == "orbit_probe"
    # legacy free-form spec is auto-wrapped into DSL geometry
    assert model.objects[0].spec.geometry["radius"] == 1.2
    assert model.objects[0].spec.dsl_version == "1.0"


def test_scene_codegen_model_accepts_dsl_spec():
    payload = {
        "version": "0.1",
        "objects": [
            {
                "object_id": "wave_demo",
                "code_key": "wave_beam",
                "spec": {
                    "dsl_version": "1.0",
                    "kind": "SPECIAL_MOTION",
                    "geometry": {"length": 4.0},
                    "style": {"color": "BLUE"},
                    "motion": {"omega": 2.0},
                    "effects": {},
                    "meta": {},
                },
                "motion_span_s": 5.0,
            }
        ],
    }
    model = SceneCodegenPlan.model_validate(payload)
    assert model.objects[0].spec.kind == "special_motion"


def test_scene_codegen_model_rejects_invalid_dsl_kind():
    payload = {
        "version": "0.1",
        "objects": [
            {
                "object_id": "wave_demo",
                "code_key": "wave_beam",
                "spec": {
                    "dsl_version": "1.0",
                    "kind": "invalid_kind",
                    "geometry": {"length": 4.0},
                    "style": {},
                    "motion": {},
                    "effects": {},
                    "meta": {},
                },
                "motion_span_s": None,
            }
        ],
    }
    with pytest.raises(Exception):
        SceneCodegenPlan.model_validate(payload)


def test_scene_codegen_model_rejects_duplicate_object_id():
    payload = {
        "version": "0.1",
        "objects": [
            {"object_id": "o1", "code_key": "k1", "spec": {}, "motion_span_s": None},
            {"object_id": "o1", "code_key": "k2", "spec": {}, "motion_span_s": None},
        ],
    }
    with pytest.raises(Exception):
        SceneCodegenPlan.model_validate(payload)
