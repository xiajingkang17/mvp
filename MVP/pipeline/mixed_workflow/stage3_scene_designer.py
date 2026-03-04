from __future__ import annotations

from .common import (
    Any,
    LLMClient,
    Path,
    _load_json,
    _normalize_scene_design_payload,
    _write_text,
    build_scene_design_user_prompt,
    build_scene_designs_batch_user_prompt,
    json,
    validate_scene_boundary_alignment,
)

def generate_scene_design(
    client: LLMClient,
    *,
    requirement: str,
    drawing_brief: dict[str, Any],
    scene: dict[str, Any],
    prev_scene: dict[str, Any] | None = None,
    next_scene: dict[str, Any] | None = None,
    previous_scene_design: dict[str, Any] | None = None,
    plan: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], str]:
    """
    为单个 scene 生成“分镜级设计稿”。
    返回：(design_json, raw_text)
    """

    system = client.load_stage_system_prompt("scene_designer")
    prompt_user = build_scene_design_user_prompt(
        requirement=requirement,
        drawing_brief=drawing_brief,
        scene=scene,
        prev_scene=prev_scene,
        next_scene=next_scene,
        plan=plan,
    )
    data, raw = client.generate_json(stage_key="scene_designer", system_prompt=system, user_prompt=prompt_user)

    # 强制对齐 scene_id / class_name（避免后续 codegen/渲染找不到类）
    expected_scene_id = str(scene.get("scene_id") or "").strip()
    expected_class = str(scene.get("class_name") or "").strip()
    if expected_scene_id:
        data["scene_id"] = expected_scene_id
    if expected_class:
        data["class_name"] = expected_class

    # 把规划信息也带上，方便后续“单文件”代码生成整合
    for key in ("goal", "key_points", "duration_s"):
        if key in scene and key not in data:
            data[key] = scene.get(key)

    data = _normalize_scene_design_payload(data, scene=scene)
    validate_scene_boundary_alignment(scene=scene, scene_design=data, previous_scene_design=previous_scene_design)

    return data, raw


def generate_scene_designs_batch(
    client: LLMClient,
    *,
    requirement: str,
    drawing_brief: dict[str, Any],
    plan: dict[str, Any],
) -> tuple[dict[str, Any], str]:
    """
    一次调用 LLM3，为整片 scenes 生成设计稿。
    返回：
    - payload: {"video_title": str, "scenes": [...]}
    - raw_text
    """

    system = client.load_stage_system_prompt("scene_designer")
    prompt_user = build_scene_designs_batch_user_prompt(
        requirement=requirement,
        drawing_brief=drawing_brief,
        plan=plan,
    )
    data, raw = client.generate_json(stage_key="scene_designer", system_prompt=system, user_prompt=prompt_user)

    if isinstance(data, dict) and not isinstance(data.get("scenes"), list):
        if str(data.get("scene_id") or "").strip():
            raise RuntimeError(
                "LLM3 多 scene 模式返回了单个 scene 顶层 JSON；期望格式应为 "
                '{"video_title": "...", "scenes": [...]}'
            )

    planned_scenes = plan.get("scenes") or []
    if not isinstance(planned_scenes, list):
        planned_scenes = []
    planned_scenes = [scene for scene in planned_scenes if isinstance(scene, dict)]

    raw_scenes = data.get("scenes") if isinstance(data.get("scenes"), list) else []
    raw_by_id = {
        str(scene.get("scene_id") or "").strip(): scene
        for scene in raw_scenes
        if isinstance(scene, dict) and str(scene.get("scene_id") or "").strip()
    }

    normalized_scenes: list[dict[str, Any]] = []
    previous_scene_design: dict[str, Any] | None = None
    for idx, scene in enumerate(planned_scenes, start=1):
        sid = str(scene.get("scene_id") or "").strip() or f"scene_{idx:02d}"
        raw_scene = raw_by_id.get(sid)
        if raw_scene is None and idx - 1 < len(raw_scenes) and isinstance(raw_scenes[idx - 1], dict):
            raw_scene = raw_scenes[idx - 1]
        if not isinstance(raw_scene, dict):
            raw_scene = {}

        raw_scene = dict(raw_scene)
        raw_scene["scene_id"] = sid
        if str(scene.get("class_name") or "").strip():
            raw_scene["class_name"] = str(scene.get("class_name") or "").strip()
        for key in ("goal", "key_points", "duration_s"):
            if key in scene and key not in raw_scene:
                raw_scene[key] = scene.get(key)

        normalized = _normalize_scene_design_payload(raw_scene, scene=scene)
        validate_scene_boundary_alignment(scene=scene, scene_design=normalized, previous_scene_design=previous_scene_design)
        normalized_scenes.append(normalized)
        previous_scene_design = normalized

    payload = {
        "video_title": str(data.get("video_title") or plan.get("video_title") or "").strip(),
        "scenes": normalized_scenes,
    }
    return payload, raw



def write_split_scene_design_files(
    *,
    out_dir: Path,
    scene_designs: dict[str, Any],
) -> None:
    scenes = scene_designs.get("scenes") or []
    if not isinstance(scenes, list):
        return
    for scene in scenes:
        if not isinstance(scene, dict):
            continue
        sid = str(scene.get("scene_id") or "").strip()
        if not sid:
            continue
        scene_dir = out_dir / "scenes" / sid
        scene_dir.mkdir(parents=True, exist_ok=True)
        _write_text(scene_dir / "design.json", json.dumps(scene, ensure_ascii=False, indent=2) + "\n")


def write_split_scene_layout_files(
    *,
    out_dir: Path,
    scene_layouts: dict[str, Any],
) -> None:
    scenes = scene_layouts.get("scenes") or []
    if not isinstance(scenes, list):
        return
    for scene in scenes:
        if not isinstance(scene, dict):
            continue
        sid = str(scene.get("scene_id") or "").strip()
        if not sid:
            continue
        scene_dir = out_dir / "scenes" / sid
        scene_dir.mkdir(parents=True, exist_ok=True)
        _write_text(scene_dir / "layout.json", json.dumps(scene, ensure_ascii=False, indent=2) + "\n")


def stage_scene_designs(
    client: LLMClient,
    *,
    requirement: str,
    drawing_brief: dict[str, Any],
    plan: dict[str, Any],
    out_dir: Path,
    scene_id: str = "",
) -> dict[str, Any]:
    """
    生成 stage3 设计稿。
    - 全量运行时：一次调用 LLM3，输出整片 scenes，并按 scene 拆分落盘
    - 单 scene 运行时：只重跑指定 scene，并更新聚合文件与拆分文件
    """

    all_scenes = plan.get("scenes") or []
    if not isinstance(all_scenes, list) or not all_scenes:
        raise RuntimeError("stage2_scene_plan.json 中缺少 scenes 列表")
    all_scenes = [sc for sc in all_scenes if isinstance(sc, dict)]

    wanted = scene_id.strip()
    _remove_path(out_dir / "object_boundary_memory.json")
    scene_index_by_id = {
        str(sc.get("scene_id") or "").strip(): idx for idx, sc in enumerate(all_scenes)
    }

    if not wanted:
        payload, raw = generate_scene_designs_batch(
            client,
            requirement=requirement,
            drawing_brief=drawing_brief,
            plan=plan,
        )
        _write_text(out_dir / "stage3_scene_designs_raw.txt", raw)
        client.save_json(out_dir / "stage3_scene_designs.json", payload)
        write_split_scene_design_files(out_dir=out_dir, scene_designs=payload)
        return payload

    current_scene = next((sc for sc in all_scenes if str(sc.get("scene_id") or "").strip() == wanted), None)
    if current_scene is None:
        raise RuntimeError(f"未找到 scene_id={wanted}（请检查 stage2_scene_plan.json）")

    existing_payload: dict[str, Any] = {}
    stage3_path = out_dir / "stage3_scene_designs.json"
    if stage3_path.exists():
        try:
            existing_payload = _load_json(stage3_path)
        except Exception:  # noqa: BLE001
            existing_payload = {}

    existing_scenes = existing_payload.get("scenes") if isinstance(existing_payload, dict) else None
    existing_map = {
        str(it.get("scene_id") or "").strip(): it
        for it in existing_scenes
        if isinstance(existing_scenes, list) and isinstance(it, dict) and str(it.get("scene_id") or "").strip()
    } if isinstance(existing_scenes, list) else {}

    full_idx = scene_index_by_id.get(wanted, -1)
    prev_scene = all_scenes[full_idx - 1] if full_idx > 0 else None
    previous_scene_design = (
        existing_map.get(str(prev_scene.get("scene_id") or "").strip())
        if isinstance(prev_scene, dict)
        else None
    )
    next_scene = all_scenes[full_idx + 1] if 0 <= full_idx + 1 < len(all_scenes) else None

    design, raw = generate_scene_design(
        client,
        requirement=requirement,
        drawing_brief=drawing_brief,
        scene=current_scene,
        prev_scene=prev_scene,
        next_scene=next_scene,
        previous_scene_design=previous_scene_design,
        plan=plan,
    )
    _write_text(out_dir / f"stage3_{wanted}_raw.txt", raw)
    existing_map[wanted] = design

    ordered: list[dict[str, Any]] = []
    seen: set[str] = set()
    for sc in all_scenes:
        sid = str(sc.get("scene_id") or "").strip()
        if not sid:
            continue
        it = existing_map.get(sid)
        if it is None:
            continue
        ordered.append(it)
        seen.add(sid)
    for sid, it in existing_map.items():
        if sid not in seen:
            ordered.append(it)

    payload = {
        "video_title": str(existing_payload.get("video_title") or plan.get("video_title") or "").strip(),
        "scenes": ordered,
    }
    client.save_json(stage3_path, payload)
    write_split_scene_design_files(out_dir=out_dir, scene_designs=payload)
    return payload


