from __future__ import annotations

import argparse
import json
from pathlib import Path

from pipeline.env import load_dotenv
from schema.scene_plan_models import LayoutSpec, ObjectSpec, ScenePlan, SceneSpec


def main() -> int:
    parser = argparse.ArgumentParser(description="合并 draft+layout 生成 scene_plan.json")
    parser.add_argument("--case", default="cases/demo_001", help="case 目录，例如 cases/demo_001")
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
            objects[object_id] = ObjectSpec(
                type=str(obj.get("type", "")),
                params=dict(obj.get("params") or {}),
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
        layout_spec = LayoutSpec(type=str(layout_obj.get("type", "")), slots=dict(layout_obj.get("slots") or {}))

        scene_spec = SceneSpec(
            id=str(scene_id),
            intent=intent,
            layout=layout_spec,
            actions=list(s.get("actions") or []),
            keep=list(s.get("keep") or []),
            notes=notes,
        )
        scenes.append(scene_spec)

    plan = ScenePlan(
        version="0.1",
        meta={"manim_version": "0.19.1"},
        objects=objects,
        scenes=scenes,
    )

    out_path.write_text(json.dumps(plan.model_dump(mode="json"), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(str(out_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
