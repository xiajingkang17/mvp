from __future__ import annotations

from pathlib import Path

from pipeline.run_llm_codegen import (
    _apply_manifest_to_plan,
    _collect_custom_targets,
    _extract_python_code,
    _validate_codegen_runtime,
)
from schema.scene_codegen_models import SceneCodegenPlan
from schema.scene_plan_models import ScenePlan


def test_extract_python_code_from_fenced_block():
    raw = """```python
from manim import Dot
BUILDERS = {"moving_dot": lambda spec: Dot()}
UPDATERS = {}
```"""
    code = _extract_python_code(raw)
    assert "BUILDERS" in code
    assert "```" not in code


def test_apply_manifest_to_plan_updates_custom_object_params():
    plan_data = {
        "version": "0.1",
        "meta": {"name": "demo"},
        "objects": {
            "c1": {"type": "CustomObject", "params": {}},
            "t1": {"type": "TextBlock", "params": {"text": "x"}},
        },
        "scenes": [],
    }
    manifest = SceneCodegenPlan.model_validate(
        {
            "version": "0.1",
            "objects": [
                {
                    "object_id": "c1",
                    "code_key": "moving_dot",
                    "spec": {"radius": 0.2},
                    "motion_span_s": 3.5,
                }
            ],
        }
    )

    updated = _apply_manifest_to_plan(plan_data, manifest, code_file="llm_codegen.py")
    params = updated["objects"]["c1"]["params"]
    assert params["code_key"] == "moving_dot"
    assert params["spec"]["dsl_version"] == "1.0"
    assert params["spec"]["geometry"] == {"radius": 0.2}
    assert params["motion_span_s"] == 3.5
    assert params["code_file"] == "llm_codegen.py"


def test_validate_codegen_runtime_rejects_banned_import(tmp_path: Path):
    manifest = SceneCodegenPlan.model_validate(
        {
            "version": "0.1",
            "objects": [{"object_id": "c1", "code_key": "x1", "spec": {}, "motion_span_s": None}],
        }
    )
    code = "import os\nBUILDERS = {}\nUPDATERS = {}\n"
    errors = _validate_codegen_runtime(code, manifest, case_dir=tmp_path)
    assert any("Banned import" in msg for msg in errors)


def test_validate_codegen_runtime_accepts_minimal_valid_code(tmp_path: Path):
    manifest = SceneCodegenPlan.model_validate(
        {
            "version": "0.1",
            "objects": [{"object_id": "c1", "code_key": "moving_dot", "spec": {}, "motion_span_s": 2.0}],
        }
    )
    code = "\n".join(
        [
            "from manim import Dot",
            "",
            "def build_moving_dot(spec):",
            "    return Dot()",
            "",
            "def update_moving_dot(mobj, t, spec):",
            "    mobj.shift([0.0, 0.0, 0.0])",
            "",
            "BUILDERS = {'moving_dot': build_moving_dot}",
            "UPDATERS = {'moving_dot': update_moving_dot}",
        ]
    )
    errors = _validate_codegen_runtime(code, manifest, case_dir=tmp_path)
    assert errors == []


def test_collect_custom_targets_prefers_explicit_marked_objects():
    plan = ScenePlan.model_validate(
        {
            "version": "0.1",
            "meta": {},
            "objects": {
                "c_marked": {
                    "type": "CustomObject",
                    "params": {"codegen_request": {"enabled": True, "scope": "motion", "intent": "x"}},
                },
                "c_unmarked": {"type": "CustomObject", "params": {}},
                "t1": {"type": "TextBlock", "params": {"text": "x"}},
            },
            "scenes": [],
        }
    )
    targets, markers, mode = _collect_custom_targets(plan)
    assert mode == "marked_only"
    assert set(targets.keys()) == {"c_marked"}
    assert "c_marked" in markers


def test_collect_custom_targets_falls_back_to_all_when_no_marked_enabled():
    plan = ScenePlan.model_validate(
        {
            "version": "0.1",
            "meta": {},
            "objects": {
                "c1": {"type": "CustomObject", "params": {}},
                "c2": {
                    "type": "CustomObject",
                    "params": {"codegen_request": {"enabled": False, "scope": "object", "intent": "skip"}},
                },
            },
            "scenes": [],
        }
    )
    targets, markers, mode = _collect_custom_targets(plan)
    assert mode == "all_custom_objects"
    assert set(targets.keys()) == {"c1", "c2"}
    assert "c2" in markers
