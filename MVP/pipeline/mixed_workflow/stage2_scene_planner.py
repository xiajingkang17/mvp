from __future__ import annotations

from .common import (
    Any,
    LLMClient,
    Path,
    _SCENE_WORKFLOW_STEPS,
    _clean_str_list,
    _write_text,
    json,
    validate_scene_plan_workflow,
)

def stage_scene_plan(
    client: LLMClient,
    *,
    requirement: str,
    analysis: dict[str, Any],
    problem_solving: dict[str, Any],
    out_dir: Path,
) -> dict[str, Any]:
    system = client.load_stage_system_prompt("scene_planner")
    user = (
        "【用户需求】\n"
        f"{requirement.strip()}\n\n"
        "【分析与前置探索 JSON】\n"
        f"{json.dumps(analysis, ensure_ascii=False, indent=2)}\n\n"
        "【完整解题 JSON】\n"
        f"{json.dumps(problem_solving, ensure_ascii=False, indent=2)}\n"
    )
    data, raw = client.generate_json(stage_key="scene_planner", system_prompt=system, user_prompt=user)
    _write_text(out_dir / "stage2_scene_plan_raw.txt", raw)

    # 轻量补全：保证 scenes 可用（避免后续因为字段缺失直接崩）
    total_s = analysis.get("total_duration_s")
    try:
        total_s_num = float(total_s) if total_s is not None else 120.0
    except Exception:  # noqa: BLE001
        total_s_num = 120.0

    scenes = data.get("scenes")
    if not isinstance(scenes, list):
        scenes = []

    video_title = str(data.get("video_title") or "").strip()
    opening_strategy = str(data.get("opening_strategy") or "").strip().lower()
    if opening_strategy not in {"preview_first", "model_first", "hybrid"}:
        opening_strategy = ""
    question_structure = str(data.get("question_structure") or "").strip().lower()
    if question_structure not in {"single_question", "multi_question"}:
        question_structure = ""

    normalized: list[dict[str, Any]] = []
    for idx, sc in enumerate(scenes, start=1):
        if not isinstance(sc, dict):
            continue
        scene_id = str(sc.get("scene_id") or "").strip() or f"scene_{idx:02d}"
        class_name = str(sc.get("class_name") or "").strip() or f"Scene{idx:02d}"
        scene_goal = str(sc.get("scene_goal") or "").strip()
        key_points = sc.get("key_points")
        if not isinstance(key_points, list):
            key_points = []
        duration_s = sc.get("duration_s")
        try:
            duration_num = float(duration_s) if duration_s is not None else 0.0
        except Exception:  # noqa: BLE001
            duration_num = 0.0

        workflow_step = str(sc.get("workflow_step") or "").strip().lower()
        if workflow_step not in _SCENE_WORKFLOW_STEPS:
            workflow_step = ""

        question_scope = str(sc.get("question_scope") or "").strip()
        entry_requirement = str(sc.get("entry_requirement") or "").strip()
        scene_outputs = _clean_str_list(sc.get("scene_outputs"))
        handoff_to_next = str(sc.get("handoff_to_next") or "").strip()
        layout_prompt = str(sc.get("layout_prompt") or "").strip()

        panels: list[dict[str, Any]] = []
        raw_panels = sc.get("panels")
        if isinstance(raw_panels, list):
            for panel in raw_panels:
                if not isinstance(panel, dict):
                    continue
                panels.append(
                    {
                        "panel_id": str(panel.get("panel_id") or "").strip(),
                        "panel_role": str(panel.get("panel_role") or "").strip(),
                        "zone_role": str(panel.get("zone_role") or "").strip(),
                    }
                )

        beat_sequence: list[dict[str, Any]] = []
        raw_beats = sc.get("beat_sequence")
        if isinstance(raw_beats, list):
            for beat in raw_beats:
                if not isinstance(beat, dict):
                    continue
                try:
                    beat_duration = float(beat.get("duration_s"))
                except (TypeError, ValueError):
                    beat_duration = 0.0
                raw_panel_changes = beat.get("panel_changes")
                panel_changes: list[dict[str, Any]] = []
                if isinstance(raw_panel_changes, list):
                    for change in raw_panel_changes:
                        if not isinstance(change, dict):
                            continue
                        panel_changes.append(
                            {
                                "panel_id": str(change.get("panel_id") or "").strip(),
                                "action": str(change.get("action") or "").strip(),
                            }
                        )
                beat_sequence.append(
                    {
                        "beat_id": str(beat.get("beat_id") or "").strip(),
                        "intent": str(beat.get("intent") or "").strip(),
                        "panel_changes": panel_changes,
                        "duration_s": beat_duration,
                        "optional_prompt": str(beat.get("optional_prompt") or "").strip(),
                    }
                )

        normalized.append(
            {
                "scene_id": scene_id,
                "class_name": class_name,
                "scene_goal": scene_goal,
                "key_points": [str(x) for x in key_points if str(x).strip()],
                "duration_s": duration_num,
                "workflow_step": workflow_step,
                "question_scope": question_scope,
                "entry_requirement": entry_requirement,
                "scene_outputs": scene_outputs,
                "handoff_to_next": handoff_to_next,
                "layout_prompt": layout_prompt,
                "panels": panels,
                "beat_sequence": beat_sequence,
            }
        )

    if normalized:
        # 若模型没分配时长，按总时长均分一个兜底
        if sum(sc.get("duration_s", 0.0) for sc in normalized) <= 1e-6:
            per = max(5.0, total_s_num / len(normalized))
            for sc in normalized:
                sc["duration_s"] = round(per, 2)
        data = {
            "video_title": video_title,
            "opening_strategy": opening_strategy,
            "question_structure": question_structure,
            "scenes": normalized,
        }

    validate_scene_plan_workflow(plan=data)

    client.save_json(out_dir / "stage2_scene_plan.json", data)
    return data


