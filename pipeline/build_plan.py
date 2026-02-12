from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from layout.params import sanitize_params
from layout.templates import build_template
from pipeline.env import load_dotenv
from schema.scene_plan_models import LayoutSpec, ObjectSpec, PedagogyPlan, ScenePlan, SceneSpec


_CJK_RE = re.compile(r"[\u3400-\u9fff]")
_SLOT_TOKEN_SPLIT_RE = re.compile(r"[\s_-]+")
_GRID_TYPE_RE = re.compile(r"^grid_(\d+)x(\d+)$")


def _contains_cjk(text: str) -> bool:
    return bool(_CJK_RE.search(text))


def _normalize_draft_object(obj: dict) -> tuple[str, dict]:
    object_type = str(obj.get("type", ""))
    params = dict(obj.get("params") or {})

    if object_type == "TextBlock":
        text = params.get("text")
        if text is None:
            text = params.get("content", "")
        params["text"] = str(text)
        params.pop("content", None)
        return object_type, params

    if object_type == "Formula":
        latex = params.get("latex")
        if latex is None:
            latex = params.get("content", "")
        latex = str(latex)
        if _contains_cjk(latex):
            return "TextBlock", {"text": latex}
        params["latex"] = latex
        params.pop("content", None)
        return object_type, params

    return object_type, params


def _normalize_layout_slots(slots: object) -> dict[str, str]:
    if not isinstance(slots, dict):
        return {}

    normalized: dict[str, str] = {}
    for raw_key, raw_value in slots.items():
        if raw_key is None or raw_value is None:
            continue

        key = str(raw_key).strip()
        if not key:
            continue

        if isinstance(raw_value, str):
            value = raw_value.strip()
        elif isinstance(raw_value, (int, float, bool)):
            value = str(raw_value)
        else:
            continue

        if not value:
            continue
        normalized[key] = value

    return normalized


def _normalize_slot_token(token: str) -> str:
    return _SLOT_TOKEN_SPLIT_RE.sub("", token.strip().lower())


def _canonicalize_layout_slots(template_type: str, slots: dict[str, str]) -> dict[str, str]:
    if not template_type or not slots:
        return slots

    try:
        template = build_template(template_type)
    except Exception:  # noqa: BLE001
        return slots

    normalized_to_canonical: dict[str, str] = {}

    def _register_alias(alias: str, canonical: str) -> None:
        token = _normalize_slot_token(alias)
        if token and token not in normalized_to_canonical:
            normalized_to_canonical[token] = canonical

    for slot_id in template.slots:
        normalized = _normalize_slot_token(slot_id)
        if normalized not in normalized_to_canonical:
            normalized_to_canonical[normalized] = slot_id

    grid_match = _GRID_TYPE_RE.match(template_type)
    if grid_match:
        cols = int(grid_match.group(1))
        rows = int(grid_match.group(2))
        ordered_slots = list(template.slot_order)
        for idx, slot_id in enumerate(ordered_slots, start=1):
            _register_alias(f"c{idx}", slot_id)
            _register_alias(f"cell{idx}", slot_id)
            _register_alias(f"slot{idx}", slot_id)
        for r in range(1, rows + 1):
            for c in range(1, cols + 1):
                idx = (r - 1) * cols + c
                if 1 <= idx <= len(ordered_slots):
                    _register_alias(f"r{r}c{c}", ordered_slots[idx - 1])

    resolved: dict[str, str] = {}
    for slot_id, object_id in slots.items():
        key = slot_id.strip()
        if key in template.slots:
            canonical = key
        else:
            canonical = normalized_to_canonical.get(_normalize_slot_token(key), key)
        if canonical in resolved:
            continue
        resolved[canonical] = object_id
    return resolved


def _normalize_roles(raw_roles: Any) -> dict[str, str]:
    if not isinstance(raw_roles, dict):
        return {}
    result: dict[str, str] = {}
    for raw_key, raw_value in raw_roles.items():
        key = str(raw_key).strip()
        value = str(raw_value).strip()
        if key and value:
            result[key] = value
    return result


def _normalize_str_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [s for s in (str(x).strip() for x in value if x is not None) if s]


def _normalize_actions(raw_actions: Any) -> list[dict[str, Any]]:
    if not isinstance(raw_actions, list):
        return []

    normalized: list[dict[str, Any]] = []
    for raw_item in raw_actions:
        if not isinstance(raw_item, dict):
            continue

        op = str(raw_item.get("op", "")).strip().lower()
        if op == "wait":
            duration = raw_item.get("duration", 0.0)
            try:
                duration_value = float(duration)
            except (TypeError, ValueError):
                duration_value = 0.0
            normalized.append({"op": "wait", "duration": max(0.0, duration_value)})
            continue

        if op == "play":
            item: dict[str, Any] = {
                "op": "play",
                "anim": raw_item.get("anim", ""),
                "src": raw_item.get("src"),
                "dst": raw_item.get("dst"),
                "duration": raw_item.get("duration"),
                "kwargs": raw_item.get("kwargs") if isinstance(raw_item.get("kwargs"), dict) else {},
            }

            raw_targets = raw_item.get("targets")
            if raw_targets is None:
                raw_targets = raw_item.get("target")

            if isinstance(raw_targets, list):
                targets = [s for s in (str(x).strip() for x in raw_targets if x is not None) if s]
            elif raw_targets is None:
                targets = []
            else:
                one = str(raw_targets).strip()
                targets = [one] if one else []

            item["targets"] = targets
            normalized.append(item)
            continue

        # Unknown op: keep as-is so upstream validation can report a clear error.
        normalized.append(dict(raw_item))

    return normalized


def main() -> int:
    parser = argparse.ArgumentParser(description="Merge draft+layout into scene_plan.json")
    parser.add_argument("--case", default="cases/demo_001", help="Case directory, e.g. cases/demo_001")
    args = parser.parse_args()

    load_dotenv()

    case_dir = Path(args.case)
    draft_path = case_dir / "scene_draft.json"
    layout_path = case_dir / "scene_layout.json"
    out_path = case_dir / "scene_plan.json"

    draft = json.loads(draft_path.read_text(encoding="utf-8"))
    layout = json.loads(layout_path.read_text(encoding="utf-8"))

    draft_scenes = {s.get("id"): s for s in (draft.get("scenes") or []) if s.get("id")}
    layout_scenes = layout.get("scenes") or []

    objects: dict[str, ObjectSpec] = {}
    for s in draft.get("scenes") or []:
        for obj in s.get("objects") or []:
            object_id = obj.get("id")
            if not object_id:
                continue
            if object_id in objects:
                continue
            normalized_type, normalized_params = _normalize_draft_object(obj)
            objects[object_id] = ObjectSpec(
                type=normalized_type,
                params=normalized_params,
                style=dict(obj.get("style") or {}),
                priority=int(obj.get("priority", 2)),
                anchor=obj.get("anchor"),
                z_index=obj.get("z_index"),
            )

    scenes: list[SceneSpec] = []
    for s in layout_scenes:
        scene_id = s.get("id")
        if not scene_id:
            continue

        draft_scene = draft_scenes.get(scene_id, {})
        intent = s.get("intent") or draft_scene.get("intent")
        notes = s.get("notes") or draft_scene.get("notes")

        layout_obj = s.get("layout") or {}
        layout_type = str(layout_obj.get("type", ""))
        layout_slots = _canonicalize_layout_slots(layout_type, _normalize_layout_slots(layout_obj.get("slots")))
        layout_spec = LayoutSpec(
            type=layout_type,
            slots=layout_slots,
            params=sanitize_params(layout_type, dict(layout_obj.get("params") or {})),
        )

        scene_spec = SceneSpec(
            id=str(scene_id),
            intent=intent,
            layout=layout_spec,
            actions=_normalize_actions(s.get("actions")),
            keep=list(s.get("keep") or []),
            notes=notes,
            goal=s.get("goal") or draft_scene.get("goal"),
            modules=_normalize_str_list(s.get("modules") or draft_scene.get("modules")),
            roles=_normalize_roles(s.get("roles") or draft_scene.get("roles")),
            new_symbols=_normalize_str_list(s.get("new_symbols") or draft_scene.get("new_symbols")),
            is_check_scene=bool(s.get("is_check_scene") or draft_scene.get("is_check_scene")),
        )
        scenes.append(scene_spec)

    pedagogy_raw = draft.get("pedagogy_plan")
    pedagogy_plan = PedagogyPlan.model_validate(pedagogy_raw) if isinstance(pedagogy_raw, dict) else None

    plan = ScenePlan(
        version="0.1",
        meta={"manim_version": "0.19.1"},
        objects=objects,
        scenes=scenes,
        pedagogy_plan=pedagogy_plan,
    )

    out_path.write_text(json.dumps(plan.model_dump(mode="json"), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(str(out_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
