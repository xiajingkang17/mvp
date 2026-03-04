from __future__ import annotations

from .common import (
    Any,
    LLMClient,
    Path,
    _normalize_scene_layout_payload,
    _write_text,
    build_scene_layouts_batch_user_prompt,
    validate_scene_layout_contract,
)

def generate_scene_layouts_batch(
    client: LLMClient,
    *,
    requirement: str,
    drawing_brief: dict[str, Any],
    plan: dict[str, Any],
    scene_designs: dict[str, Any],
) -> tuple[dict[str, Any], str]:
    system = client.load_stage_system_prompt("layout_designer")
    prompt_user = build_scene_layouts_batch_user_prompt(
        requirement=requirement,
        drawing_brief=drawing_brief,
        plan=plan,
        scene_designs=scene_designs,
    )
    data, raw = client.generate_json(stage_key="layout_designer", system_prompt=system, user_prompt=prompt_user)

    if isinstance(data, dict) and not isinstance(data.get("scenes"), list):
        if str(data.get("scene_id") or "").strip():
            raise RuntimeError(
                "LLM3.5 多 scene 模式返回了单个 scene 顶层 JSON；期望格式应为 "
                '{"video_title": "...", "scenes": [...]}'
            )

    planned_scenes = plan.get("scenes") or []
    if not isinstance(planned_scenes, list):
        planned_scenes = []
    planned_scenes = [scene for scene in planned_scenes if isinstance(scene, dict)]

    design_map = {
        str(item.get("scene_id") or "").strip(): item
        for item in (scene_designs.get("scenes") or [])
        if isinstance(item, dict) and str(item.get("scene_id") or "").strip()
    }
    raw_scenes = data.get("scenes") if isinstance(data.get("scenes"), list) else []
    raw_by_id = {
        str(item.get("scene_id") or "").strip(): item
        for item in raw_scenes
        if isinstance(item, dict) and str(item.get("scene_id") or "").strip()
    }

    normalized_scenes: list[dict[str, Any]] = []
    for idx, scene in enumerate(planned_scenes, start=1):
        sid = str(scene.get("scene_id") or "").strip() or f"scene_{idx:02d}"
        raw_scene = raw_by_id.get(sid)
        if raw_scene is None and idx - 1 < len(raw_scenes) and isinstance(raw_scenes[idx - 1], dict):
            raw_scene = raw_scenes[idx - 1]
        if not isinstance(raw_scene, dict):
            raw_scene = {}

        normalized = _normalize_scene_layout_payload(
            dict(raw_scene),
            scene=scene,
            scene_design=design_map.get(sid, {}),
        )
        validate_scene_layout_contract(
            scene=scene,
            scene_design={"scene_id": sid, "layout_contract": normalized.get("layout_contract") or {}},
        )
        normalized_scenes.append(normalized)

    payload = {
        "video_title": str(data.get("video_title") or plan.get("video_title") or "").strip(),
        "scenes": normalized_scenes,
    }
    return payload, raw



def stage_scene_layouts(
    client: LLMClient,
    *,
    requirement: str,
    drawing_brief: dict[str, Any],
    plan: dict[str, Any],
    scene_designs: dict[str, Any],
    out_dir: Path,
) -> dict[str, Any]:
    payload, raw = generate_scene_layouts_batch(
        client,
        requirement=requirement,
        drawing_brief=drawing_brief,
        plan=plan,
        scene_designs=scene_designs,
    )
    _write_text(out_dir / "stage35_scene_layouts_raw.txt", raw)
    client.save_json(out_dir / "stage35_scene_layouts.json", payload)
    write_split_scene_layout_files(out_dir=out_dir, scene_layouts=payload)
    return payload


