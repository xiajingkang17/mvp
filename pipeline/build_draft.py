from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from schema.scene_draw_models import SceneDrawPlan
from schema.scene_semantic_models import SceneSemanticPlan


def merge_semantic_and_draw(
    *,
    semantic_data: dict[str, Any],
    draw_data: dict[str, Any],
) -> dict[str, Any]:
    semantic = SceneSemanticPlan.model_validate(semantic_data)
    draw = SceneDrawPlan.model_validate(draw_data)

    draw_scene_by_id = {scene.id: scene for scene in draw.scenes}
    errors: list[str] = []
    draft_scenes: list[dict[str, Any]] = []

    for scene_index, scene in enumerate(semantic.scenes):
        draw_scene = draw_scene_by_id.get(scene.id)
        draw_graph_by_object_id: dict[str, Any] = {}
        if draw_scene is not None:
            for item in draw_scene.composites:
                draw_graph_by_object_id[item.object_id] = item.graph.model_dump(mode="json")

        object_type_by_id = {obj.id: obj.type for obj in scene.objects}
        if draw_scene is not None:
            for object_id in draw_graph_by_object_id:
                otype = object_type_by_id.get(object_id)
                if otype is None:
                    errors.append(
                        f"scene '{scene.id}' draw composite '{object_id}' not found in scene_semantic objects"
                    )
                elif otype != "CompositeObject":
                    errors.append(
                        f"scene '{scene.id}' draw composite '{object_id}' is not CompositeObject (found: {otype})"
                    )

        scene_objects: list[dict[str, Any]] = []
        for object_index, obj in enumerate(scene.objects):
            item = obj.model_dump(mode="json")
            if obj.type != "CompositeObject":
                scene_objects.append(item)
                continue

            graph = draw_graph_by_object_id.get(obj.id)
            if graph is None:
                errors.append(
                    f"scenes[{scene_index}].objects[{object_index}] ({obj.id}) missing graph in scene_draw.json"
                )
                scene_objects.append(item)
                continue

            params = dict(obj.params or {})
            params["graph"] = graph
            item["params"] = params
            scene_objects.append(item)

        draft_scenes.append(
            {
                "id": scene.id,
                "intent": scene.intent,
                "goal": scene.goal,
                "modules": list(scene.modules),
                "roles": dict(scene.roles),
                "new_symbols": list(scene.new_symbols),
                "is_check_scene": bool(scene.is_check_scene),
                "notes": scene.notes,
                "narrative_storyboard": scene.narrative_storyboard.model_dump(mode="json"),
                "objects": scene_objects,
            }
        )

    for draw_scene in draw.scenes:
        if draw_scene.id not in {scene.id for scene in semantic.scenes}:
            errors.append(f"scene_draw scene '{draw_scene.id}' not found in scene_semantic.json")

    if errors:
        raise ValueError("\n".join(errors))

    result: dict[str, Any] = {
        "version": semantic.version,
        "scenes": draft_scenes,
    }
    if semantic.pedagogy_plan is not None:
        result["pedagogy_plan"] = semantic.pedagogy_plan.model_dump(mode="json")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Merge scene_semantic.json + scene_draw.json into scene_draft.json")
    parser.add_argument("--case", default="cases/demo_001", help="Case directory, e.g. cases/demo_001")
    parser.add_argument("--semantic", default=None, help="Optional scene_semantic.json path")
    parser.add_argument("--draw", default=None, help="Optional scene_draw.json path")
    parser.add_argument("--out", default=None, help="Optional output path (default: case/scene_draft.json)")
    args = parser.parse_args()

    case_dir = Path(args.case)
    semantic_path = Path(args.semantic) if args.semantic else (case_dir / "scene_semantic.json")
    draw_path = Path(args.draw) if args.draw else (case_dir / "scene_draw.json")
    out_path = Path(args.out) if args.out else (case_dir / "scene_draft.json")

    semantic_data = json.loads(semantic_path.read_text(encoding="utf-8"))
    draw_data = json.loads(draw_path.read_text(encoding="utf-8"))
    merged = merge_semantic_and_draw(semantic_data=semantic_data, draw_data=draw_data)
    out_path.write_text(json.dumps(merged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(str(out_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
