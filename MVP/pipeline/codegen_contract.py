from __future__ import annotations

import re
from typing import Any


def _identifier(text: str, *, prefix: str) -> str:
    value = re.sub(r"[^A-Za-z0-9_]+", "_", str(text).strip().lower())
    value = re.sub(r"_+", "_", value).strip("_")
    if not value:
        value = prefix
    if value[0].isdigit():
        value = f"{prefix}_{value}"
    return value


def _dedupe(name: str, used: set[str]) -> str:
    if name not in used:
        used.add(name)
        return name
    idx = 2
    while True:
        candidate = f"{name}_{idx}"
        if candidate not in used:
            used.add(candidate)
            return candidate
        idx += 1


def _collect_step_ids(scene_design: dict[str, Any]) -> list[str]:
    steps = scene_design.get("steps") or []
    if not isinstance(steps, list):
        return []

    result: list[str] = []
    for idx, step in enumerate(steps, start=1):
        if not isinstance(step, dict):
            continue
        step_id = str(step.get("step_id") or "").strip() or f"step_{idx:02d}"
        result.append(step_id)
    return result


def _append_object_ids(result: list[str], seen: set[str], values: Any) -> None:
    if isinstance(values, str):
        value = values.strip()
        if value and value not in seen:
            result.append(value)
            seen.add(value)
        return

    if isinstance(values, dict):
        for key in ("id", "object_id", "target_id", "source_id"):
            value = str(values.get(key) or "").strip()
            if value and value not in seen:
                result.append(value)
                seen.add(value)
        return

    if isinstance(values, list):
        for item in values:
            _append_object_ids(result, seen, item)


def _collect_object_ids(scene_design: dict[str, Any]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()

    registry = scene_design.get("object_registry") or []
    if isinstance(registry, list):
        for item in registry:
            _append_object_ids(result, seen, item)

    entry_state = scene_design.get("entry_state") or {}
    if isinstance(entry_state, dict):
        _append_object_ids(result, seen, entry_state.get("objects_on_screen"))

    exit_state = scene_design.get("exit_state") or {}
    if isinstance(exit_state, dict):
        _append_object_ids(result, seen, exit_state.get("objects_on_screen"))

    steps = scene_design.get("steps") or []
    if isinstance(steps, list):
        for step in steps:
            if not isinstance(step, dict):
                continue
            object_ops = step.get("object_ops") or {}
            if not isinstance(object_ops, dict):
                continue
            for key in ("create", "update", "remove", "keep"):
                _append_object_ids(result, seen, object_ops.get(key))

    return result


def build_codegen_interface_contract(
    *,
    plan: dict[str, Any],
    scene_designs: dict[str, Any],
    preferred_class_name: str = "MainScene",
) -> dict[str, Any]:
    scenes = scene_designs.get("scenes") or []
    if not isinstance(scenes, list):
        scenes = []

    plan_scenes = plan.get("scenes") or []
    if not isinstance(plan_scenes, list):
        plan_scenes = []
    plan_by_id = {
        str(scene.get("scene_id") or "").strip(): scene
        for scene in plan_scenes
        if isinstance(scene, dict)
    }

    used_scene_methods: set[str] = set()
    used_motion_methods: set[str] = set()
    entries: list[dict[str, Any]] = []

    for idx, scene_design in enumerate(scenes, start=1):
        if not isinstance(scene_design, dict):
            continue

        scene_id = str(scene_design.get("scene_id") or "").strip() or f"scene_{idx:02d}"
        scene_plan = plan_by_id.get(scene_id, {})
        safe_scene = _identifier(scene_id, prefix="scene")
        scene_method_name = _dedupe(f"scene_{safe_scene}", used_scene_methods)
        motion_method_name = _dedupe(f"motion_{safe_scene}", used_motion_methods)

        entries.append(
            {
                "scene_index": idx,
                "scene_id": scene_id,
                "title": str(scene_design.get("title") or scene_plan.get("title") or "").strip(),
                "scene_method_name": scene_method_name,
                "motion_method_name": motion_method_name,
                "step_ids": _collect_step_ids(scene_design),
                "object_ids": _collect_object_ids(scene_design),
                "has_motion_contract": isinstance(scene_design.get("motion_contract"), dict),
            }
        )

    return {
        "preferred_class_name": preferred_class_name,
        "runtime_contract": {
            "objects_registry_attr": "objects",
            "scene_state_attr": "scene_state",
            "motion_cache_attr": "motion_cache",
            "subtitle_object_id": "current_subtitle",
            "allowed_top_level_helpers": [
                "reset_scene",
                "prepare_scene_entry",
                "fit_in_zone",
                "place_in_zone",
                "layout_formula_group",
                "register_obj",
                "remove_registered_obj",
                "cleanup_step",
                "cleanup_scene",
                "show_subtitle",
                "run_step",
            ],
            "scene_method_signature": "def <scene_method_name>(self):",
            "motion_method_signature": "def <motion_method_name>(self, step_id):",
            "shared_state_access": {
                "objects": "self.objects",
                "scene_state": "self.scene_state",
                "motion_cache": "self.motion_cache",
            },
        },
        "construct_order": [entry["scene_method_name"] for entry in entries],
        "scenes": entries,
    }
