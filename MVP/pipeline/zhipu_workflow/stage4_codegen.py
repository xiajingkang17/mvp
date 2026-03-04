from __future__ import annotations

from .common import (
    Any,
    LLMClient,
    PROMPTS_DIR,
    Path,
    _build_llm4e_system_prompt,
    _normalize_codegen_bundle_payload,
    _write_codegen_bundle_fragments,
    _write_text,
    assemble_existing_llm4_fragments,
    build_codegen_interface_contract,
    json,
)

def stage_codegen_video(
    client: LLMClient,
    *,
    stage1_problem_solving: dict[str, Any],
    stage1_drawing_brief: dict[str, Any],
    plan: dict[str, Any],
    scene_designs: dict[str, Any],
    scene_layouts: dict[str, Any] | None,
    out_dir: Path,
) -> tuple[str, str]:
    """
    framework 由程序复制，scene/motion 方法由单次批量 codegen 产出，
    最终仍由程序装配成一个可直接运行的单文件：scene.py（单一 Scene 类）。
    返回：(class_name, code)
    """

    scenes = scene_designs.get("scenes") or []
    if not isinstance(scenes, list) or not scenes:
        raise RuntimeError("scene_designs.scenes 为空，无法执行批量 codegen")

    scene_design_by_id = {
        str(scene.get("scene_id") or "").strip(): scene for scene in scenes if isinstance(scene, dict)
    }
    layout_scenes = scene_layouts.get("scenes") if isinstance(scene_layouts, dict) else []
    scene_layout_by_id = {
        str(scene.get("scene_id") or "").strip(): scene for scene in layout_scenes if isinstance(layout_scenes, list) and isinstance(scene, dict)
    } if isinstance(layout_scenes, list) else {}
    plan_scenes = plan.get("scenes") or []
    if not isinstance(plan_scenes, list):
        plan_scenes = []
    plan_by_id = {
        str(scene.get("scene_id") or "").strip(): scene for scene in plan_scenes if isinstance(scene, dict)
    }

    interface_contract = build_codegen_interface_contract(
        plan=plan,
        scene_designs=scene_designs,
        preferred_class_name="MainScene",
    )
    _write_text(
        out_dir / "code_interface_contract.json",
        json.dumps(interface_contract, ensure_ascii=False, indent=2) + "\n",
    )
    _write_text(
        out_dir / "system_prompt.md",
        (
            "# Batch LLM4 orchestration\n"
            "- framework: llm4/framework/ (copied from prompts/llm4e_batch_codegen/execution_helpers.py)\n"
            "- bundle: llm4/batch/ (single LLM call returning all scene/motion fragments)\n"
            "- scenes: llm4/scenes/<scene_id>/ (written programmatically from bundle payload)\n"
            "- motion: llm4/motion/<scene_id>/ (written programmatically from bundle payload)\n"
            "- assemble: llm4/assemble/ (programmatic template assembly)\n"
            "- interface_contract: llm4/code_interface_contract.json\n"
        ),
    )

    framework_dir = out_dir / "framework"
    framework_template = PROMPTS_DIR / "llm4e_batch_codegen" / "execution_helpers.py"
    framework_code = _normalize_manim_ce_api(framework_template.read_text(encoding="utf-8")).strip() + "\n"
    _write_text(
        framework_dir / "system_prompt.md",
        "# Programmatic framework\nCopied from prompts/llm4e_batch_codegen/execution_helpers.py.\n",
    )
    _write_text(framework_dir / "framework_raw.txt", "Programmatic framework copy; no LLM output.\n")
    _write_text(framework_dir / "framework_fragment.py", framework_code)

    batch_dir = out_dir / "batch"
    batch_payload = {
        "role": "batch_codegen",
        "interface_contract": interface_contract,
        "stage1_problem_solving": stage1_problem_solving,
        "stage1_drawing_brief": stage1_drawing_brief,
        "scenes": [],
    }

    for scene_entry in interface_contract.get("scenes") or []:
        if not isinstance(scene_entry, dict):
            continue

        scene_id = str(scene_entry.get("scene_id") or "").strip()
        scene_design = scene_design_by_id.get(scene_id)
        if not isinstance(scene_design, dict):
            raise RuntimeError(f"scene_designs 中缺少 scene_id={scene_id}")
        scene_layout = scene_layout_by_id.get(scene_id, {})
        merged_scene_design = dict(scene_design)
        if isinstance(scene_layout, dict):
            layout_contract = scene_layout.get("layout_contract")
            if isinstance(layout_contract, dict):
                merged_scene_design["layout_contract"] = layout_contract

        scene_plan = plan_by_id.get(scene_id, {})
        batch_payload["scenes"].append(
            {
                "scene_contract": scene_entry,
                "scene_plan_scene": scene_plan,
                "scene_design": merged_scene_design,
                "scene_layout": scene_layout,
            }
        )

    system, component_groups, component_paths = _build_llm4e_system_prompt(
        client,
        stage1_problem_solving=stage1_problem_solving,
        stage1_drawing_brief=stage1_drawing_brief,
        plan=plan,
        scene_designs=scene_designs,
        scene_layouts=scene_layouts,
    )
    _write_text(batch_dir / "system_prompt.md", system.strip() + "\n")
    _write_text(
        batch_dir / "component_refs.json",
        json.dumps(
            {
                "component_groups": component_groups,
                "component_paths": component_paths,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    user = json.dumps(batch_payload, ensure_ascii=False, indent=2)
    data, raw = client.generate_json(
        stage_key="codegen_bundle",
        system_prompt=system,
        user_prompt=user,
        max_continue_rounds=3,
        repair_rounds=2,
    )
    _write_text(batch_dir / "codegen_bundle_raw.txt", raw)

    bundle_payload = _normalize_codegen_bundle_payload(data, interface_contract=interface_contract)
    _write_text(batch_dir / "codegen_bundle.json", json.dumps(bundle_payload, ensure_ascii=False, indent=2) + "\n")
    _write_codegen_bundle_fragments(out_dir=out_dir, bundle_payload=bundle_payload)

    return assemble_existing_llm4_fragments(out_dir=out_dir)


