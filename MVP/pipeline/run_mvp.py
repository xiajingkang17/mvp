from __future__ import annotations

import ast
import argparse
import json
import re
import shutil
import sys
import textwrap
import time
import unicodedata
from pathlib import Path
from typing import Any

# 允许两种运行方式：
# 1) 推荐：在 MVP/ 目录内执行：python run_mvp.py
# 2) 兼容：直接执行：python pipeline/run_mvp.py
#
# 注意：第二种方式下需要手动把 MVP 根目录加入 sys.path，保证能正确导入 package。
if __package__ in {None, ""}:
    _mvp_root = Path(__file__).resolve().parents[1]
    if str(_mvp_root) not in sys.path:
        sys.path.insert(0, str(_mvp_root))

    from pipeline.codegen_contract import build_codegen_interface_contract  # noqa: E402
    from pipeline.config import ERROR_DIR, PROMPTS_DIR, RUNS_DIR  # noqa: E402
    from pipeline.llm_client import LLMClient, LLMStage  # noqa: E402
    from pipeline.llm.types import ProviderName  # noqa: E402
    from pipeline.run_layout import RunLayout  # noqa: E402
    from pipeline.static_checks import run_static_checks  # noqa: E402
    from pipeline.rendering import (  # noqa: E402
        detect_scene_classes,
        render_scene,
    )
else:
    from .codegen_contract import build_codegen_interface_contract  # noqa: E402
    from .config import ERROR_DIR, PROMPTS_DIR, RUNS_DIR  # noqa: E402
    from .llm_client import LLMClient, LLMStage  # noqa: E402
    from .llm.types import ProviderName  # noqa: E402
    from .run_layout import RunLayout  # noqa: E402
    from .static_checks import run_static_checks  # noqa: E402
    from .rendering import (  # noqa: E402
        detect_scene_classes,
        render_scene,
    )


def _slugify(text: str, *, max_len: int = 48) -> str:
    s = re.sub(r"\s+", "_", text.strip())
    s = re.sub(r"[^A-Za-z0-9_\\-\\u4e00-\\u9fff]+", "", s)
    s = s.strip("_")
    return (s[:max_len] or "run").strip("_")


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _remove_path(path: Path) -> None:
    if not path.exists():
        return
    if path.is_dir():
        shutil.rmtree(path)
        return
    path.unlink()


def _reset_dir(path: Path) -> None:
    _remove_path(path)
    path.mkdir(parents=True, exist_ok=True)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _split_analyst_payload(data: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    payload = dict(data or {})
    problem_solving = payload.get("problem_solving")
    if not isinstance(problem_solving, dict):
        problem_solving = {}

    drawing_brief = payload.get("particle_motion_brief")
    if not isinstance(drawing_brief, dict):
        drawing_brief = {}

    analysis = {
        key: value
        for key, value in payload.items()
        if key not in {"problem_solving", "particle_motion_brief"}
    }
    return analysis, problem_solving, drawing_brief


def assemble_analyst_payload(
    *,
    analysis: dict[str, Any] | None,
    problem_solving: dict[str, Any] | None,
    drawing_brief: dict[str, Any] | None,
) -> dict[str, Any]:
    payload = dict(analysis or {})
    payload["problem_solving"] = dict(problem_solving or {})
    payload["particle_motion_brief"] = dict(drawing_brief or {})
    return payload


def load_stage1_analysis(*, layout: RunLayout, path: Path | None = None) -> dict[str, Any]:
    if path is not None:
        return _load_json(path)
    if layout.stage1_analysis_json.exists():
        return _load_json(layout.stage1_analysis_json)
    if layout.stage1_json.exists():
        analysis, _problem_solving, _drawing_brief = _split_analyst_payload(_load_json(layout.stage1_json))
        return analysis
    raise FileNotFoundError(f"missing llm1 analysis output: {layout.stage1_analysis_json}")


def load_stage1_problem_solving(*, layout: RunLayout) -> dict[str, Any]:
    if layout.stage1_problem_solving_json.exists():
        return _load_json(layout.stage1_problem_solving_json)
    if layout.stage1_json.exists():
        _analysis, problem_solving, _drawing_brief = _split_analyst_payload(_load_json(layout.stage1_json))
        return problem_solving
    raise FileNotFoundError(f"missing llm1 problem solving output: {layout.stage1_problem_solving_json}")


def load_stage1_drawing_brief(*, layout: RunLayout) -> dict[str, Any]:
    if layout.stage1_drawing_brief_json.exists():
        return _load_json(layout.stage1_drawing_brief_json)
    if layout.stage1_json.exists():
        _analysis, _problem_solving, drawing_brief = _split_analyst_payload(_load_json(layout.stage1_json))
        return drawing_brief
    raise FileNotFoundError(f"missing llm1 drawing brief output: {layout.stage1_drawing_brief_json}")


def load_analyst_bundle(
    *,
    layout: RunLayout,
    analyst_json: Path | None = None,
) -> dict[str, Any]:
    if analyst_json is not None:
        return _load_json(analyst_json)

    analysis_path = layout.stage1_analysis_json
    problem_solving_path = layout.stage1_problem_solving_json
    drawing_brief_path = layout.stage1_drawing_brief_json

    if analysis_path.exists() and problem_solving_path.exists():
        analysis = _load_json(analysis_path)
        problem_solving = _load_json(problem_solving_path)
        drawing_brief = _load_json(drawing_brief_path) if drawing_brief_path.exists() else {}
        return assemble_analyst_payload(
            analysis=analysis,
            problem_solving=problem_solving,
            drawing_brief=drawing_brief,
        )

    legacy = layout.stage1_json
    if legacy.exists():
        return _load_json(legacy)

    raise FileNotFoundError(
        f"missing llm1 outputs: {analysis_path}, {problem_solving_path}"
    )


def _extract_python_code(text: str) -> str:
    code = text.strip()
    if "```" in code:
        m = re.search(r"```(?:python)?\s*(.*?)```", code, flags=re.DOTALL | re.IGNORECASE)
        if m:
            code = m.group(1).strip()
    return code


def _normalize_manim_ce_api(code: str) -> str:
    """
    把常见旧版 manim API 规范化到 Manim CE 可用写法。
    这里先做保守替换，优先解决高频阻断项。
    """

    normalized = code
    normalized = re.sub(r"\bShowCreation\s*\(", "Create(", normalized)
    return normalized


def _source_segment(text: str, node: ast.AST) -> str:
    segment = ast.get_source_segment(text, node)
    if segment is not None:
        return segment

    start = getattr(node, "lineno", None)
    end = getattr(node, "end_lineno", None)
    if start is None or end is None:
        return ""
    lines = text.splitlines()
    return "\n".join(lines[start - 1 : end])


def _strip_module_docstring(nodes: list[ast.stmt]) -> list[ast.stmt]:
    if not nodes:
        return nodes
    first = nodes[0]
    if isinstance(first, ast.Expr) and isinstance(getattr(first, "value", None), ast.Constant):
        if isinstance(first.value.value, str):
            return nodes[1:]
    return nodes


def _extract_framework_fragment_parts(code: str) -> tuple[str, str]:
    module = ast.parse(code)
    body = _strip_module_docstring(list(module.body))

    imports: list[str] = []
    helpers: list[str] = []
    for node in body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            imports.append(_source_segment(code, node).strip())
            continue
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            helpers.append(_source_segment(code, node).rstrip())
            continue
        raise ValueError(f"framework fragment 包含不允许的顶层节点: {type(node).__name__}")

    if not helpers:
        raise ValueError("framework fragment 为空，未生成任何 helper")

    imports_code = "\n".join(part for part in imports if part).strip()
    helpers_code = "\n\n".join(part for part in helpers if part).strip()
    return imports_code, helpers_code


def _make_motion_stub(method_name: str) -> str:
    return (
        f"def {method_name}(self, step_id):\n"
        "    return []\n"
    )


def _extract_method_fragment(
    code: str,
    *,
    expected_name: str,
    fragment_label: str,
    allow_stub: bool = False,
) -> str:
    cleaned = _extract_python_code(code).strip()
    if not cleaned:
        if allow_stub:
            return _make_motion_stub(expected_name)
        raise ValueError(f"{fragment_label} 为空")

    try:
        module = ast.parse(cleaned)
    except SyntaxError:
        if allow_stub and cleaned.strip("`\r\n\t ") == "":
            return _make_motion_stub(expected_name)
        raise

    body = _strip_module_docstring(list(module.body))
    funcs = [node for node in body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
    if len(funcs) != 1:
        if allow_stub and cleaned.strip("`\r\n\t ") == "":
            return _make_motion_stub(expected_name)
        raise ValueError(f"{fragment_label} 必须只包含一个顶层方法，当前为 {len(funcs)} 个")

    for node in body:
        if node is funcs[0]:
            continue
        if isinstance(node, ast.Pass):
            continue
        raise ValueError(f"{fragment_label} 包含额外顶层节点: {type(node).__name__}")

    func = funcs[0]
    if func.name != expected_name:
        raise ValueError(f"{fragment_label} 方法名不匹配: 期望 {expected_name}，实际 {func.name}")
    return _source_segment(cleaned, func).rstrip() + "\n"


def _build_program_assembled_scene(
    *,
    class_name: str,
    construct_order: list[str],
    framework_code: str,
    scene_methods: list[str],
    motion_methods: list[str],
) -> str:
    imports_code, helper_code = _extract_framework_fragment_parts(framework_code)

    construct_lines = [
        "def construct(self):",
        "    self.objects = {}",
        "    self.scene_state = {}",
        "    self.motion_cache = {}",
    ]
    construct_lines.extend(f"    self.{method_name}()" for method_name in construct_order if method_name.strip())
    construct_block = "\n".join(construct_lines)

    class_parts = [construct_block]
    class_parts.extend(method.rstrip() for method in scene_methods if method.strip())
    class_parts.extend(method.rstrip() for method in motion_methods if method.strip())
    class_body = "\n\n".join(class_parts).rstrip()
    class_code = f"class {class_name}(Scene):\n{textwrap.indent(class_body, '    ')}\n"

    parts = []
    if imports_code:
        parts.append(imports_code)
    if helper_code:
        parts.append(helper_code)
    parts.append(class_code.rstrip())
    return "\n\n\n".join(part for part in parts if part.strip()) + "\n"


def assemble_existing_llm4_fragments(*, out_dir: Path) -> tuple[str, str]:
    contract_path = out_dir / "code_interface_contract.json"
    if not contract_path.exists():
        raise FileNotFoundError(f"missing interface contract: {contract_path}")

    interface_contract = _load_json(contract_path)
    class_name = str(interface_contract.get("preferred_class_name") or "MainScene").strip() or "MainScene"

    framework_path = out_dir / "framework" / "framework_fragment.py"
    if not framework_path.exists():
        raise FileNotFoundError(f"missing framework fragment: {framework_path}")
    framework_code = framework_path.read_text(encoding="utf-8")

    scene_methods: list[str] = []
    motion_methods: list[str] = []
    manifest_scenes: list[dict[str, Any]] = []
    manifest_motion: list[dict[str, Any]] = []

    for entry in interface_contract.get("scenes") or []:
        if not isinstance(entry, dict):
            continue

        scene_id = str(entry.get("scene_id") or "").strip()
        scene_method_name = str(entry.get("scene_method_name") or "").strip()
        motion_method_name = str(entry.get("motion_method_name") or "").strip()

        scene_path = out_dir / "scenes" / scene_id / "scene_method.py"
        if not scene_path.exists():
            raise FileNotFoundError(f"missing scene fragment: {scene_path}")
        scene_code = scene_path.read_text(encoding="utf-8")
        scene_methods.append(
            _extract_method_fragment(
                scene_code,
                expected_name=scene_method_name,
                fragment_label=f"scene fragment {scene_id}",
            )
        )
        manifest_scenes.append(
            {"scene_id": scene_id, "scene_method_name": scene_method_name, "path": str(scene_path)}
        )

        motion_path = out_dir / "motion" / scene_id / "motion_method.py"
        if not motion_path.exists():
            raise FileNotFoundError(f"missing motion fragment: {motion_path}")
        motion_code = motion_path.read_text(encoding="utf-8")
        motion_methods.append(
            _extract_method_fragment(
                motion_code,
                expected_name=motion_method_name,
                fragment_label=f"motion fragment {scene_id}",
                allow_stub=True,
            )
        )
        manifest_motion.append(
            {"scene_id": scene_id, "motion_method_name": motion_method_name, "path": str(motion_path)}
        )

    final_code = _build_program_assembled_scene(
        class_name=class_name,
        construct_order=[str(name).strip() for name in interface_contract.get("construct_order") or []],
        framework_code=framework_code,
        scene_methods=scene_methods,
        motion_methods=motion_methods,
    )

    assemble_dir = out_dir / "assemble"
    _write_text(
        assemble_dir / "system_prompt.md",
        (
            "# Programmatic assemble\n"
            "LLM4 final assembly is deterministic.\n"
            "- imports + helpers: framework/framework_fragment.py\n"
            "- class shell + construct order: code_interface_contract.json\n"
            "- scene methods: scenes/<scene_id>/scene_method.py\n"
            "- motion methods: motion/<scene_id>/motion_method.py\n"
        ),
    )
    _write_text(assemble_dir / "assemble_raw.txt", "Programmatic assemble; no LLM output.\n")
    _write_text(
        assemble_dir / "assemble_manifest.json",
        json.dumps(
            {
                "class_name": class_name,
                "construct_order": interface_contract.get("construct_order") or [],
                "scene_fragments": manifest_scenes,
                "motion_fragments": manifest_motion,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    _write_text(assemble_dir / "scene.py", final_code)
    _write_text(out_dir / "stage4_codegen_raw.txt", final_code)

    classes = detect_scene_classes(final_code)
    if classes and class_name not in classes:
        class_name = classes[0]
    if not classes:
        class_name = "MainScene"

    return class_name, final_code + ("\n" if not final_code.endswith("\n") else "")


def _safe_name(text: str) -> str:
    value = re.sub(r"[^A-Za-z0-9._-]+", "_", str(text).strip())
    value = value.strip("._-")
    return value or "unknown"


def _clean_str_list(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []
    return [str(x).strip() for x in values if str(x).strip()]


_SCENE_WORKFLOW_STEPS = {
    "problem_intake",
    "preview",
    "goal_lock",
    "model",
    "method_choice",
    "derive",
    "check",
    "recap",
    "transfer",
}
_SCENE_PANEL_ROLES = {
    "problem_panel",
    "preview_panel",
    "question_map_panel",
    "diagram_panel",
    "derivation_panel",
    "checkpoint_panel",
    "summary_panel",
}
_SCENE_ZONE_ROLES = {
    "top",
    "main",
    "left",
    "right",
    "formula",
    "summary",
    "subtitle",
}
_SCENE_BEAT_PANEL_ACTIONS = {
    "show",
    "hide",
    "highlight",
    "update",
    "freeze",
}


def _scene_brief(scene: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(scene, dict):
        return {}
    return {
        "scene_id": str(scene.get("scene_id") or "").strip(),
        "class_name": str(scene.get("class_name") or "").strip(),
        "scene_goal": str(scene.get("scene_goal") or "").strip(),
        "workflow_step": str(scene.get("workflow_step") or "").strip(),
        "question_scope": str(scene.get("question_scope") or "").strip(),
        "entry_requirement": str(scene.get("entry_requirement") or "").strip(),
        "key_points": _clean_str_list(scene.get("key_points")),
        "scene_outputs": _clean_str_list(scene.get("scene_outputs")),
        "handoff_to_next": str(scene.get("handoff_to_next") or "").strip(),
        "layout_prompt": str(scene.get("layout_prompt") or "").strip(),
        "panels": scene.get("panels") if isinstance(scene.get("panels"), list) else [],
        "beat_sequence": scene.get("beat_sequence") if isinstance(scene.get("beat_sequence"), list) else [],
        "duration_s": scene.get("duration_s"),
    }


def validate_scene_plan_workflow(*, plan: dict[str, Any]) -> None:
    if not isinstance(plan, dict):
        raise ValueError("stage2 scene plan must be a JSON object")

    if not str(plan.get("video_title") or "").strip():
        raise ValueError("stage2 scene plan is missing video_title")

    opening_strategy = str(plan.get("opening_strategy") or "").strip()
    if opening_strategy not in {"preview_first", "model_first", "hybrid"}:
        raise ValueError("stage2 scene plan has invalid opening_strategy")

    question_structure = str(plan.get("question_structure") or "").strip()
    if question_structure not in {"single_question", "multi_question"}:
        raise ValueError("stage2 scene plan has invalid question_structure")

    scenes = plan.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        raise ValueError("stage2 scene plan is missing scenes")

    for scene in scenes:
        if not isinstance(scene, dict):
            continue
        sid = str(scene.get("scene_id") or "").strip() or "scene_unknown"
        workflow_step = str(scene.get("workflow_step") or "").strip()
        if workflow_step not in _SCENE_WORKFLOW_STEPS:
            raise ValueError(f"{sid} has invalid workflow_step")
        if not str(scene.get("question_scope") or "").strip():
            raise ValueError(f"{sid} is missing question_scope")
        if not str(scene.get("scene_goal") or "").strip():
            raise ValueError(f"{sid} is missing scene_goal")
        if not str(scene.get("entry_requirement") or "").strip():
            raise ValueError(f"{sid} is missing entry_requirement")
        key_points = scene.get("key_points")
        if not isinstance(key_points, list) or not [x for x in key_points if str(x).strip()]:
            raise ValueError(f"{sid} is missing key_points")
        scene_outputs = scene.get("scene_outputs")
        if not isinstance(scene_outputs, list) or not [x for x in scene_outputs if str(x).strip()]:
            raise ValueError(f"{sid} is missing scene_outputs")
        if not str(scene.get("handoff_to_next") or "").strip():
            raise ValueError(f"{sid} is missing handoff_to_next")
        if not str(scene.get("layout_prompt") or "").strip():
            raise ValueError(f"{sid} is missing layout_prompt")

        panels = scene.get("panels")
        if not isinstance(panels, list) or not panels:
            raise ValueError(f"{sid} is missing panels")
        panel_ids: set[str] = set()
        for panel in panels:
            if not isinstance(panel, dict):
                raise ValueError(f"{sid} has invalid panel entry")
            panel_id = str(panel.get("panel_id") or "").strip()
            panel_role = str(panel.get("panel_role") or "").strip()
            zone_role = str(panel.get("zone_role") or "").strip()
            if not panel_id:
                raise ValueError(f"{sid} has panel without panel_id")
            if panel_id in panel_ids:
                raise ValueError(f"{sid} has duplicate panel_id: {panel_id}")
            panel_ids.add(panel_id)
            if panel_role not in _SCENE_PANEL_ROLES:
                raise ValueError(f"{sid} has invalid panel_role: {panel_role}")
            if zone_role not in _SCENE_ZONE_ROLES:
                raise ValueError(f"{sid} has invalid zone_role: {zone_role}")

        beat_sequence = scene.get("beat_sequence")
        if not isinstance(beat_sequence, list) or not beat_sequence:
            raise ValueError(f"{sid} is missing beat_sequence")
        seen_beats: set[str] = set()
        for beat in beat_sequence:
            if not isinstance(beat, dict):
                raise ValueError(f"{sid} has invalid beat entry")
            beat_id = str(beat.get("beat_id") or "").strip()
            intent = str(beat.get("intent") or "").strip()
            if not beat_id:
                raise ValueError(f"{sid} has beat without beat_id")
            if beat_id in seen_beats:
                raise ValueError(f"{sid} has duplicate beat_id: {beat_id}")
            seen_beats.add(beat_id)
            if not intent:
                raise ValueError(f"{sid}:{beat_id} is missing intent")
            panel_changes = beat.get("panel_changes")
            if not isinstance(panel_changes, list) or not panel_changes:
                raise ValueError(f"{sid}:{beat_id} is missing panel_changes")
            for change in panel_changes:
                if not isinstance(change, dict):
                    raise ValueError(f"{sid}:{beat_id} has invalid panel_change entry")
                panel_id = str(change.get("panel_id") or "").strip()
                action = str(change.get("action") or "").strip()
                if panel_id not in panel_ids:
                    raise ValueError(f"{sid}:{beat_id} references unknown panel_id: {panel_id}")
                if action not in _SCENE_BEAT_PANEL_ACTIONS:
                    raise ValueError(f"{sid}:{beat_id} has invalid panel action: {action}")
            try:
                duration_num = float(beat.get("duration_s"))
            except (TypeError, ValueError):
                duration_num = 0.0
            if duration_num <= 0.0:
                raise ValueError(f"{sid}:{beat_id} has invalid duration_s")


def validate_scene_boundary_alignment(
    *,
    scene: dict[str, Any],
    scene_design: dict[str, Any],
    previous_scene_design: dict[str, Any] | None,
) -> None:
    # Scenes are intentionally isolated: no cross-scene object inheritance is allowed.
    return


_FIXED_SUBTITLE_ZONE = {
    "x0": 0.05,
    "x1": 0.95,
    "y0": 0.02,
    "y1": 0.12,
}
_SUBTITLE_ZONE_TOLERANCE = 1e-3
_SUBTITLE_MAX_LINES = 2
_SUBTITLE_MAX_UNITS_PER_LINE = 30.0
_SUBTITLE_ALLOWED_TOTAL_UNITS = _SUBTITLE_MAX_LINES * _SUBTITLE_MAX_UNITS_PER_LINE


def _to_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _normalize_layout_contract(layout: Any) -> dict[str, Any]:
    if not isinstance(layout, dict):
        layout = {}

    raw_global_rules = layout.get("global_rules") if isinstance(layout.get("global_rules"), dict) else {}
    zones: list[dict[str, Any]] = []
    for item in layout.get("zones") or []:
        if not isinstance(item, dict):
            continue
        x0 = _to_float(item.get("x0"), 0.0)
        x1 = _to_float(item.get("x1"), 0.0)
        y0 = _to_float(item.get("y0"), 0.0)
        y1 = _to_float(item.get("y1"), 0.0)
        if x1 <= x0 or y1 <= y0:
            continue
        zones.append(
            {
                "id": str(item.get("id") or "").strip(),
                "role": str(item.get("role") or "").strip(),
                "x0": x0,
                "x1": x1,
                "y0": y0,
                "y1": y1,
            }
        )

    objects: list[dict[str, Any]] = []
    for item in layout.get("objects") or []:
        if not isinstance(item, dict):
            continue
        obj_id = str(item.get("id") or "").strip()
        zone_id = str(item.get("zone") or "").strip()
        if not obj_id or not zone_id:
            continue
        objects.append(
            {
                "id": obj_id,
                "kind": str(item.get("kind") or "").strip(),
                "zone": zone_id,
                "priority": item.get("priority"),
                "max_width_ratio": item.get("max_width_ratio"),
                "max_height_ratio": item.get("max_height_ratio"),
            }
        )

    step_visibility: list[dict[str, Any]] = []
    for idx, item in enumerate(layout.get("step_visibility") or [], start=1):
        if not isinstance(item, dict):
            continue
        zone_overrides = item.get("zone_overrides") if isinstance(item.get("zone_overrides"), dict) else {}
        step_visibility.append(
            {
                "step": item.get("step") or idx,
                "layout_objects": _clean_str_list(item.get("layout_objects")),
                "zone_overrides": zone_overrides,
            }
        )

    return {
        "version": str(layout.get("version") or "v1").strip() or "v1",
        "language": str(layout.get("language") or "zh-CN").strip() or "zh-CN",
        "safe_margin": _to_float(layout.get("safe_margin"), 0.04),
        "zones": zones,
        "global_rules": {
            "avoid_overlap": bool(raw_global_rules.get("avoid_overlap", True)),
            "min_gap": _to_float(raw_global_rules.get("min_gap"), 0.02),
            "formula_stack": str(raw_global_rules.get("formula_stack") or "arrange_down").strip() or "arrange_down",
            "subtitle_reserved": bool(raw_global_rules.get("subtitle_reserved", True)),
        },
        "objects": objects,
        "step_visibility": step_visibility,
    }


def _zones_overlap(a: dict[str, Any], b: dict[str, Any]) -> bool:
    return (
        float(a["x0"]) < float(b["x1"])
        and float(a["x1"]) > float(b["x0"])
        and float(a["y0"]) < float(b["y1"])
        and float(a["y1"]) > float(b["y0"])
    )


def _subtitle_visual_units(text: str) -> float:
    total = 0.0
    for ch in str(text):
        if ch == "\n":
            continue
        if ch.isspace():
            total += 0.35
            continue
        total += 1.0 if unicodedata.east_asian_width(ch) in {"W", "F"} else 0.6
    return total


def _subtitle_line_count(text: str) -> int:
    lines = 1
    current = 0.0
    for ch in str(text):
        if ch == "\n":
            lines += 1
            current = 0.0
            continue
        units = 0.35 if ch.isspace() else (1.0 if unicodedata.east_asian_width(ch) in {"W", "F"} else 0.6)
        if current + units > _SUBTITLE_MAX_UNITS_PER_LINE:
            lines += 1
            current = units
        else:
            current += units
    return lines


def _split_long_subtitle_clause(text: str) -> list[str]:
    chunks: list[str] = []
    current: list[str] = []
    current_units = 0.0
    for ch in str(text).strip():
        if ch == "\n":
            candidate = "".join(current).strip()
            if candidate:
                chunks.append(candidate)
            current = []
            current_units = 0.0
            continue
        units = 0.35 if ch.isspace() else (1.0 if unicodedata.east_asian_width(ch) in {"W", "F"} else 0.6)
        if current and current_units + units > _SUBTITLE_ALLOWED_TOTAL_UNITS:
            candidate = "".join(current).strip()
            if candidate:
                chunks.append(candidate)
            current = [ch]
            current_units = units
        else:
            current.append(ch)
            current_units += units
    candidate = "".join(current).strip()
    if candidate:
        chunks.append(candidate)
    return chunks


def _split_narration_segments(value: Any) -> list[str]:
    if isinstance(value, list):
        raise ValueError("steps[*].narration must be a string; runtime subtitle splitting is handled by LLM4 helpers.")

    raw = str(value or "").strip()
    if not raw:
        return []

    punctuation = "，。；：？！,.;:?!"
    segments: list[str] = []
    if _subtitle_line_count(raw) <= _SUBTITLE_MAX_LINES and _subtitle_visual_units(raw) <= _SUBTITLE_ALLOWED_TOTAL_UNITS:
        segments.append(raw)
        return segments

    clauses: list[str] = []
    current: list[str] = []
    for ch in raw:
        current.append(ch)
        if ch in punctuation:
            clause = "".join(current).strip()
            if clause:
                clauses.append(clause)
            current = []
    tail = "".join(current).strip()
    if tail:
        clauses.append(tail)
    if not clauses:
        clauses = [raw]

    packed: list[str] = []
    buffer = ""
    for clause in clauses:
        candidate = f"{buffer}{clause}".strip() if not buffer else f"{buffer}{clause}"
        if (
            buffer
            and (
                _subtitle_line_count(candidate) > _SUBTITLE_MAX_LINES
                or _subtitle_visual_units(candidate) > _SUBTITLE_ALLOWED_TOTAL_UNITS
            )
        ):
            if buffer.strip():
                packed.append(buffer.strip())
            buffer = clause.strip()
        else:
            buffer = candidate.strip()
    if buffer.strip():
        packed.append(buffer.strip())

    for piece in packed:
        if _subtitle_line_count(piece) <= _SUBTITLE_MAX_LINES and _subtitle_visual_units(piece) <= _SUBTITLE_ALLOWED_TOTAL_UNITS:
            segments.append(piece)
        else:
            segments.extend(_split_long_subtitle_clause(piece))

    return [segment for segment in segments if segment]


def validate_scene_layout_contract(
    *,
    scene: dict[str, Any],
    scene_design: dict[str, Any],
) -> None:
    layout = scene_design.get("layout_contract") if isinstance(scene_design.get("layout_contract"), dict) else {}
    zones = layout.get("zones") if isinstance(layout.get("zones"), list) else []
    subtitle_zones = [zone for zone in zones if isinstance(zone, dict) and str(zone.get("role") or "").strip() == "subtitle"]
    scene_id = str(scene_design.get("scene_id") or scene.get("scene_id") or "").strip() or "<scene>"

    if len(subtitle_zones) > 1:
        raise ValueError(f"{scene_id}: layout_contract may contain at most one subtitle zone.")
    if not subtitle_zones:
        return

    subtitle_zone = subtitle_zones[0]
    for key, expected in _FIXED_SUBTITLE_ZONE.items():
        actual = _to_float(subtitle_zone.get(key), float("nan"))
        if abs(actual - expected) > _SUBTITLE_ZONE_TOLERANCE:
            raise ValueError(
                f"{scene_id}: subtitle zone must stay fixed at {_FIXED_SUBTITLE_ZONE}, got {subtitle_zone}."
            )

    global_rules = layout.get("global_rules") if isinstance(layout.get("global_rules"), dict) else {}
    if not bool(global_rules.get("subtitle_reserved")):
        raise ValueError(f"{scene_id}: layout_contract.global_rules.subtitle_reserved must be true.")

    for zone in zones:
        if not isinstance(zone, dict) or zone is subtitle_zone:
            continue
        if _zones_overlap(zone, subtitle_zone):
            raise ValueError(
                f"{scene_id}: zone '{zone.get('id')}' overlaps the reserved subtitle zone."
            )

    subtitle_zone_id = str(subtitle_zone.get("id") or "").strip()
    for item in layout.get("objects") if isinstance(layout.get("objects"), list) else []:
        if not isinstance(item, dict):
            continue
        if str(item.get("zone") or "").strip() == subtitle_zone_id:
            raise ValueError(
                f"{scene_id}: layout object '{item.get('id')}' may not occupy subtitle zone '{subtitle_zone_id}'."
            )

    for item in layout.get("step_visibility") if isinstance(layout.get("step_visibility"), list) else []:
        if not isinstance(item, dict):
            continue
        overrides = item.get("zone_overrides") if isinstance(item.get("zone_overrides"), dict) else {}
        if subtitle_zone_id in overrides or "subtitle_zone" in overrides or "subtitle" in overrides:
            raise ValueError(f"{scene_id}: step_visibility may not override subtitle zone.")

    for idx, step in enumerate(scene_design.get("steps") or [], start=1):
        if not isinstance(step, dict):
            continue
        narration_value = step.get("narration")
        narration_segments = _split_narration_segments(narration_value)
        if not narration_segments:
            continue
        for segment_idx, narration in enumerate(narration_segments, start=1):
            total_units = _subtitle_visual_units(narration)
            line_count = _subtitle_line_count(narration)
            if line_count > _SUBTITLE_MAX_LINES or total_units > _SUBTITLE_ALLOWED_TOTAL_UNITS:
                step_id = str(step.get("step_id") or "").strip() or f"step_{idx:02d}"
                segment_label = f"{step_id}[{segment_idx}]"
                raise ValueError(
                    f"{scene_id}:{segment_label} narration is too long for the fixed subtitle zone even after splitting; "
                    f"shorten the text."
                )


def build_scene_design_user_prompt(
    *,
    requirement: str,
    drawing_brief: dict[str, Any],
    scene: dict[str, Any],
    prev_scene: dict[str, Any] | None = None,
    next_scene: dict[str, Any] | None = None,
    plan: dict[str, Any] | None = None,
) -> str:
    return (
        "[用户需求]\n"
        f"{requirement.strip()}\n\n"
        "[画图提示 JSON]\n"
        f"{json.dumps(drawing_brief, ensure_ascii=False, indent=2)}\n\n"
        "[上一 Scene 摘要]\n"
        f"{json.dumps(_scene_brief(prev_scene or {}), ensure_ascii=False, indent=2)}\n\n"
        "[当前 Scene]\n"
        f"{json.dumps(scene, ensure_ascii=False, indent=2)}\n\n"
        "[下一 Scene 摘要]\n"
        f"{json.dumps(_scene_brief(next_scene or {}), ensure_ascii=False, indent=2)}\n"
    )


def build_scene_designs_batch_user_prompt(
    *,
    requirement: str,
    drawing_brief: dict[str, Any],
    plan: dict[str, Any],
) -> str:
    scenes = plan.get("scenes") or []
    if not isinstance(scenes, list):
        scenes = []

    scene_payload: list[dict[str, Any]] = []
    for scene in scenes:
        if not isinstance(scene, dict):
            continue
        payload = dict(scene)
        payload["scene_brief"] = _scene_brief(scene)
        scene_payload.append(payload)

    return (
        "[用户需求]\n"
        f"{requirement.strip()}\n\n"
        "[画图提示 JSON]\n"
        f"{json.dumps(drawing_brief, ensure_ascii=False, indent=2)}\n\n"
        "[整片 Scene 规划]\n"
        f"{json.dumps(scene_payload, ensure_ascii=False, indent=2)}\n"
    )


def _normalize_scene_design_payload(
    data: dict[str, Any],
    *,
    scene: dict[str, Any],
) -> dict[str, Any]:
    payload = dict(data or {})

    raw_registry = payload.get("object_registry")

    registry: list[dict[str, Any]] = []
    if isinstance(raw_registry, list):
        for item in raw_registry:
            if not isinstance(item, dict):
                continue
            obj_id = str(item.get("id") or "").strip()
            if not obj_id:
                continue
            registry.append(
                {
                    "id": obj_id,
                    "kind": str(item.get("kind") or "").strip(),
                    "role": str(item.get("role") or item.get("visual_role") or "").strip(),
                    "description": str(item.get("description") or "").strip(),
                }
            )

    entry_state = payload.get("entry_state") if isinstance(payload.get("entry_state"), dict) else {}
    exit_state = payload.get("exit_state") if isinstance(payload.get("exit_state"), dict) else {}

    entry_objects: list[str] = []
    entry_focus = str(
        entry_state.get("visual_focus")
        or scene.get("entry_requirement")
        or scene.get("scene_goal")
        or ""
    ).strip()

    exit_objects: list[str] = []

    raw_steps = payload.get("steps") or []
    steps: list[dict[str, Any]] = []
    if isinstance(raw_steps, list):
        for idx, step in enumerate(raw_steps, start=1):
            if not isinstance(step, dict):
                continue
            object_ops = step.get("object_ops") if isinstance(step.get("object_ops"), dict) else {}
            narration_value = step.get("narration")
            _split_narration_segments(narration_value)
            narration_text = str(narration_value or "").strip()
            create_ids = _clean_str_list(object_ops.get("create"))
            update_ids = _clean_str_list(object_ops.get("update"))
            remove_ids = _clean_str_list(object_ops.get("remove"))
            keep_ids = _clean_str_list(object_ops.get("keep"))
            end_state_objects = _clean_str_list(step.get("end_state_objects"))
            if not end_state_objects:
                end_state_objects = keep_ids
            if not keep_ids and end_state_objects:
                keep_ids = list(end_state_objects)

            steps.append(
                {
                    **step,
                    "step_id": str(step.get("step_id") or "").strip() or f"step_{idx:02d}",
                    "narration": narration_text,
                    "object_ops": {
                        "create": create_ids,
                        "update": update_ids,
                        "remove": remove_ids,
                        "keep": keep_ids,
                    },
                    "end_state_objects": end_state_objects,
                }
            )

    payload["object_registry"] = registry
    payload["entry_state"] = {
        "objects_on_screen": entry_objects,
        "visual_focus": entry_focus,
    }
    payload["steps"] = steps
    payload["exit_state"] = {
        "objects_on_screen": exit_objects,
        "handoff_intent": str(
            exit_state.get("handoff_intent")
            or scene.get("handoff_to_next")
            or ""
        ).strip(),
    }
    payload["layout_contract"] = _normalize_layout_contract(payload.get("layout_contract"))

    allowed_keys = {
        "scene_id",
        "class_name",
        "goal",
        "key_points",
        "duration_s",
        "narration",
        "on_screen_text",
        "object_registry",
        "entry_state",
        "steps",
        "exit_state",
        "layout_contract",
        "motion_contract",
    }
    return {key: value for key, value in payload.items() if key in allowed_keys}


def _write_global_llm4_error_log(
    *,
    layout: RunLayout,
    attempt: int,
    class_name: str,
    returncode: int,
    stderr: str,
    stdout: str,
) -> None:
    """
    把 llm4 渲染报错集中落盘到 MVP/error/，便于跨 run 汇总排查。
    """

    try:
        ERROR_DIR.mkdir(parents=True, exist_ok=True)
        ts = time.strftime("%Y%m%d_%H%M%S")
        ms = int((time.time() % 1) * 1000)
        run_tag = _safe_name(layout.run_dir.name)
        cls_tag = _safe_name(class_name)
        filename = f"{ts}_{ms:03d}_{run_tag}_{cls_tag}_attempt{int(attempt)}.log"
        path = ERROR_DIR / filename
        content = (
            f"time={ts}.{ms:03d}\n"
            f"run_dir={layout.run_dir}\n"
            f"scene_file={layout.llm4_scene_py}\n"
            f"class_name={class_name}\n"
            f"attempt={int(attempt)}\n"
            f"returncode={int(returncode)}\n"
            f"render_stderr_file={layout.render_stderr(attempt)}\n"
            f"render_stdout_file={layout.render_stdout(attempt)}\n\n"
            f"=== STDERR ===\n{stderr.strip()}\n\n"
            f"=== STDOUT ===\n{stdout.strip()}\n"
        )
        _write_text(path, content)
    except Exception:  # noqa: BLE001
        # 全局日志写入失败不阻断主流程
        pass


def reset_case_outputs(layout: RunLayout, *, from_stage: int) -> None:
    if from_stage <= 1:
        _reset_dir(layout.llm1_dir)
    if from_stage <= 2:
        _reset_dir(layout.llm2_dir)
    if from_stage <= 3:
        _reset_dir(layout.llm3_dir)
    if from_stage <= 4:
        _reset_dir(layout.llm4_dir)
        _remove_path(layout.exported_scene_py)
    if from_stage <= 5:
        _reset_dir(layout.llm5_dir)
        _reset_dir(layout.render_dir)
        _remove_path(layout.exported_final_mp4)

    _remove_path(layout.run_dir / "FAILED.txt")


def build_client(*, llm4_provider: ProviderName = "anthropic") -> LLMClient:
    # 复用 MVP/configs/llm.yaml 里的 stage 采样 profile
    llm4_profile_stage = {
        "codegen_scene": "codegen_scene",
        "codegen_motion": "codegen_motion",
    }
    stage_map = {
        "analyst": LLMStage(
            name="analyst",
            provider="zhipu",
            profile_stage="analyst",
            prompt_bundle="llm1_analyst",
        ),
        "scene_planner": LLMStage(
            name="scene_planner",
            provider="zhipu",
            profile_stage="scene_planner",
            prompt_bundle="llm2_scene_planner",
        ),
        "scene_designer": LLMStage(
            name="scene_designer",
            provider="zhipu",
            profile_stage="scene_designer",
            prompt_bundle="llm3_scene_designer",
        ),
        "codegen_scene": LLMStage(
            name="codegen_scene",
            provider=llm4_provider,
            profile_stage=llm4_profile_stage["codegen_scene"],
            prompt_bundle="llm4b_scene_codegen",
        ),
        "codegen_motion": LLMStage(
            name="codegen_motion",
            provider=llm4_provider,
            profile_stage=llm4_profile_stage["codegen_motion"],
            prompt_bundle="llm4c_motion_codegen",
        ),
        "fixer": LLMStage(
            name="fixer",
            provider="zhipu",
            profile_stage="fixer",
            prompt_bundle="llm5_fixer",
        ),
    }
    return LLMClient(prompts_dir=PROMPTS_DIR, stage_map=stage_map)


def stage_analyst(client: LLMClient, *, requirement: str, out_dir: Path) -> dict[str, Any]:
    system = client.load_stage_system_prompt("analyst")
    user = requirement.strip()
    data, raw = client.generate_json(stage_key="analyst", system_prompt=system, user_prompt=user)
    _write_text(out_dir / "stage1_analyst_raw.txt", raw)
    analysis, problem_solving, drawing_brief = _split_analyst_payload(data)
    client.save_json(out_dir / "stage1_analysis.json", analysis)
    client.save_json(out_dir / "stage1_problem_solving.json", problem_solving)
    client.save_json(out_dir / "stage1_drawing_brief.json", drawing_brief)
    return assemble_analyst_payload(
        analysis=analysis,
        problem_solving=problem_solving,
        drawing_brief=drawing_brief,
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
    validate_scene_layout_contract(scene=scene, scene_design=data)

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
        validate_scene_layout_contract(scene=scene, scene_design=normalized)
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


def stage_codegen_video(
    client: LLMClient,
    *,
    stage1_problem_solving: dict[str, Any],
    stage1_drawing_brief: dict[str, Any],
    plan: dict[str, Any],
    scene_designs: dict[str, Any],
    out_dir: Path,
) -> tuple[str, str]:
    """
    把多个 scene 的设计稿拆成 framework / scene / motion / assembler 四段 codegen，
    最终仍产出一个可直接运行的单文件：scene.py（单一 Scene 类）。
    返回：(class_name, code)
    """

    def _generate_fragment(
        *,
        stage_key: str,
        payload: dict[str, Any],
        target_dir: Path,
        raw_name: str,
        chunk_prefix: str,
        fragment_name: str,
        max_continue_rounds: int = 3,
    ) -> str:
        system = client.load_stage_system_prompt(stage_key)
        _write_text(target_dir / "system_prompt.md", system.strip() + "\n")
        user = json.dumps(payload, ensure_ascii=False, indent=2)
        merged, raw, chunks = client.generate_code(
            stage_key=stage_key,
            system_prompt=system,
            user_prompt=user,
            max_continue_rounds=max_continue_rounds,
        )
        _write_text(target_dir / raw_name, raw)
        for idx, chunk in enumerate(chunks, start=1):
            _write_text(target_dir / f"{chunk_prefix}_{idx}.txt", chunk)

        fragment = _normalize_manim_ce_api(_extract_python_code(merged)).strip() + "\n"
        _write_text(target_dir / fragment_name, fragment)
        return fragment

    scenes = scene_designs.get("scenes") or []
    if not isinstance(scenes, list) or not scenes:
        raise RuntimeError("scene_designs.scenes 为空，无法执行拆分式 codegen")

    scene_design_by_id = {
        str(scene.get("scene_id") or "").strip(): scene for scene in scenes if isinstance(scene, dict)
    }
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
            "# Split LLM4 orchestration\n"
            "- framework: llm4/framework/ (copied from prompts/llm4_codegen/execution_helpers.py)\n"
            "- scenes: llm4/scenes/<scene_id>/\n"
            "- motion: llm4/motion/<scene_id>/\n"
            "- assemble: llm4/assemble/ (programmatic template assembly)\n"
            "- interface_contract: llm4/code_interface_contract.json\n"
        ),
    )

    framework_dir = out_dir / "framework"
    framework_template = PROMPTS_DIR / "llm4_codegen" / "execution_helpers.py"
    framework_code = _normalize_manim_ce_api(framework_template.read_text(encoding="utf-8")).strip() + "\n"
    _write_text(
        framework_dir / "system_prompt.md",
        "# Programmatic framework\nCopied from prompts/llm4_codegen/execution_helpers.py.\n",
    )
    _write_text(framework_dir / "framework_raw.txt", "Programmatic framework copy; no LLM output.\n")
    _write_text(framework_dir / "framework_fragment.py", framework_code)

    scene_fragments: list[dict[str, Any]] = []
    motion_fragments: list[dict[str, Any]] = []

    for scene_entry in interface_contract.get("scenes") or []:
        if not isinstance(scene_entry, dict):
            continue

        scene_id = str(scene_entry.get("scene_id") or "").strip()
        scene_design = scene_design_by_id.get(scene_id)
        if not isinstance(scene_design, dict):
            raise RuntimeError(f"scene_designs 中缺少 scene_id={scene_id}")

        scene_plan = plan_by_id.get(scene_id, {})
        scene_dir = out_dir / "scenes" / scene_id
        motion_dir = out_dir / "motion" / scene_id

        scene_code = _generate_fragment(
            stage_key="codegen_scene",
            payload={
                "role": "scene_codegen",
                "interface_contract": interface_contract,
                "stage1_problem_solving": stage1_problem_solving,
                "stage1_drawing_brief": stage1_drawing_brief,
                "scene_contract": scene_entry,
                "scene_plan_scene": scene_plan,
                "scene_design": scene_design,
            },
            target_dir=scene_dir,
            raw_name="scene_method_raw.txt",
            chunk_prefix="scene_method_continue",
            fragment_name="scene_method.py",
            max_continue_rounds=3,
        )
        scene_fragments.append(
            {
                "scene_id": scene_id,
                "scene_method_name": scene_entry.get("scene_method_name"),
                "code": scene_code,
            }
        )

        motion_code = _generate_fragment(
            stage_key="codegen_motion",
            payload={
                "role": "motion_codegen",
                "interface_contract": interface_contract,
                "stage1_problem_solving": stage1_problem_solving,
                "stage1_drawing_brief": stage1_drawing_brief,
                "scene_contract": scene_entry,
                "scene_plan_scene": scene_plan,
                "scene_design": scene_design,
            },
            target_dir=motion_dir,
            raw_name="motion_raw.txt",
            chunk_prefix="motion_continue",
            fragment_name="motion_method.py",
            max_continue_rounds=3,
        )
        motion_fragments.append(
            {
                "scene_id": scene_id,
                "motion_method_name": scene_entry.get("motion_method_name"),
                "code": motion_code,
            }
        )

    return assemble_existing_llm4_fragments(out_dir=out_dir)


def stage_fix_code(
    client: LLMClient,
    *,
    class_name: str,
    code: str,
    stderr: str,
    scene_dir: Path,
    attempt: int,
) -> str:
    system = client.load_stage_system_prompt("fixer")
    user = (
        f"【目标类名】{class_name}\n\n"
        f"【第 {attempt} 轮错误日志】\n{stderr}\n\n"
        f"【当前代码】\n{code}\n"
    )
    merged, raw, chunks = client.generate_code(
        stage_key="fixer",
        mode="repair",
        system_prompt=system,
        user_prompt=user,
        max_continue_rounds=4,
    )
    _write_text(scene_dir / f"fix_raw_{attempt}.txt", raw)
    for idx, chunk in enumerate(chunks, start=1):
        _write_text(scene_dir / f"fix_continue_{attempt}_{idx}.txt", chunk)
    fixed = _normalize_manim_ce_api(_extract_python_code(merged))
    return fixed + "\n"


def stage_static_gate(
    client: LLMClient,
    *,
    class_name: str,
    py_file: Path,
    layout: RunLayout,
    max_rounds: int = 3,
    attempt_base: int = 1000,
) -> tuple[str, bool, str, int]:
    """
    静态闸门：先跑 py_compile + pyflakes。
    - 通过：返回 (class_name, True, report)
    - 不通过：调用 Fixer 自动修复，最多 max_rounds 轮
    """

    rounds = max(0, int(max_rounds))
    last_report = ""

    for idx in range(rounds + 1):
        check = run_static_checks(py_file)
        last_report = check.to_report()
        _write_text(layout.llm5_dir / f"static_check_{idx}.txt", last_report)

        if check.ok:
            return class_name, True, last_report, idx

        if idx >= rounds:
            return class_name, False, last_report, idx

        _write_text(layout.llm5_system_prompt, client.load_stage_system_prompt("fixer").strip() + "\n")
        fixed = stage_fix_code(
            client,
            class_name=class_name,
            code=py_file.read_text(encoding="utf-8"),
            stderr=last_report,
            scene_dir=layout.llm5_dir,
            attempt=attempt_base + idx + 1,
        )
        _write_text(py_file, fixed)
        _write_text(layout.exported_scene_py, fixed)

        classes = detect_scene_classes(fixed)
        if classes and class_name not in classes:
            class_name = classes[0]

        _write_text(
            layout.stage4_meta,
            json.dumps(
                {"class_name": class_name, "last_static_fix_round": idx + 1},
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
        )

    return class_name, False, last_report, rounds


def stage_render_fix_loop(
    client: LLMClient,
    *,
    class_name: str,
    py_file: Path,
    layout: RunLayout,
    quality: str = "l",
    render_timeout_s: int = 300,
    max_fix_rounds: int = 5,
) -> tuple[str, bool, Path | None, str, int]:
    """
    渲染失败驱动修复循环：
    - 先直接执行 manim 渲染
    - 失败则把完整日志交给 Fixer（LLM5）修复
    - 修复后再次渲染，直到成功或达到最大轮数
    """

    media_dir = layout.render_media_dir
    rounds = max(0, int(max_fix_rounds))
    last_err = ""

    for attempt in range(0, rounds + 1):
        print(f"[MVP] 渲染尝试 {attempt} ...")
        result = render_scene(
            py_file=py_file,
            class_name=class_name,
            media_dir=media_dir,
            quality=quality,  # type: ignore[arg-type]
            timeout_s=int(render_timeout_s),
        )
        _write_text(layout.render_stdout(attempt), result.stdout)
        _write_text(layout.render_stderr(attempt), result.stderr)

        if result.ok and result.mp4_path:
            final_mp4 = layout.render_final_mp4
            try:
                shutil.copyfile(result.mp4_path, final_mp4)
                shutil.copyfile(final_mp4, layout.exported_final_mp4)
            except Exception:  # noqa: BLE001
                pass
            return class_name, True, result.mp4_path, "", attempt

        last_err = (
            f"[manim returncode] {result.returncode}\n\n"
            f"【stderr】\n{(result.stderr or '').strip() or '<empty>'}\n\n"
            f"【stdout】\n{(result.stdout or '').strip() or '<empty>'}\n"
        )
        _write_text(layout.llm5_dir / f"render_error_{attempt}.txt", last_err)
        _write_global_llm4_error_log(
            layout=layout,
            attempt=attempt,
            class_name=class_name,
            returncode=result.returncode,
            stderr=result.stderr or "",
            stdout=result.stdout or "",
        )

        if attempt >= rounds:
            return class_name, False, None, last_err, attempt

        print("[MVP] 进入修复（Fixer） ...")
        _write_text(layout.llm5_system_prompt, client.load_stage_system_prompt("fixer").strip() + "\n")
        fixed = stage_fix_code(
            client,
            class_name=class_name,
            code=py_file.read_text(encoding="utf-8"),
            stderr=last_err,
            scene_dir=layout.llm5_dir,
            attempt=attempt + 1,
        )
        _write_text(py_file, fixed)
        _write_text(layout.exported_scene_py, fixed)

        classes = detect_scene_classes(fixed)
        if classes and class_name not in classes:
            class_name = classes[0]

        _write_text(
            layout.stage4_meta,
            json.dumps(
                {
                    "class_name": class_name,
                    "last_fix_attempt": attempt + 1,
                    "last_render_returncode": result.returncode,
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
        )

    return class_name, False, None, last_err, rounds


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="MVP: 多 LLM 分工 -> 最终生成单个 scene.py（优先可运行）")
    p.add_argument("-r", "--requirement", type=str, default="")
    p.add_argument("--requirement-file", type=str, default="")
    p.add_argument("--run-dir", type=str, default="")
    p.add_argument("--quality", choices=["l", "m", "h"], default="l", help="manim 渲染质量：l 最快")
    p.add_argument("--render-timeout-s", type=int, default=300, help="单个渲染任务超时（秒）")
    p.add_argument("--max-fix-rounds", type=int, default=5)
    p.add_argument("--max-static-fix-rounds", type=int, default=3, help="已废弃参数（兼容保留，不再使用）")
    p.add_argument("--no-render", action="store_true", help="只生成代码，不执行 manim 渲染")
    return p.parse_args()


def _read_requirement(args: argparse.Namespace) -> str:
    if args.requirement:
        return args.requirement.strip()
    if args.requirement_file:
        return Path(args.requirement_file).read_text(encoding="utf-8").strip()

    # 兼容：如果指定了 run_dir 且其中已有 requirement.txt，则复用
    if args.run_dir:
        req_path = Path(args.run_dir) / "requirement.txt"
        if req_path.exists():
            return req_path.read_text(encoding="utf-8").strip()

    raise SystemExit("requirement 为空：请用 -r 或 --requirement-file 提供，或指定含 requirement.txt 的 --run-dir。")


def main() -> int:
    args = parse_args()
    requirement = _read_requirement(args)

    run_id = time.strftime("%Y%m%d_%H%M%S")
    slug = _slugify(requirement)

    # Case 约定：如果 requirement-file 来自 MVP/cases/<case_name>/problem.txt，且未显式指定 --run-dir，
    # 则默认把产物落在 case 目录下（再按 llm1..llm5/render 分文件夹）。
    inferred: Path | None = None
    if not args.run_dir and args.requirement_file:
        try:
            req_path = Path(args.requirement_file).resolve()
            cases_root = (RUNS_DIR.parent / "cases").resolve()
            rel = req_path.relative_to(cases_root)
            if len(rel.parts) >= 2:
                inferred = cases_root / rel.parts[0]
        except Exception:  # noqa: BLE001
            inferred = None

    run_dir = Path(args.run_dir) if args.run_dir else (inferred or (RUNS_DIR / f"{run_id}_{slug}"))
    run_dir.mkdir(parents=True, exist_ok=True)
    layout = RunLayout.from_run_dir(run_dir)
    reset_case_outputs(layout, from_stage=1)

    print(f"[MVP] 运行目录: {run_dir}")
    _write_text(layout.requirement_txt, requirement + "\n")

    client = build_client()

    print("[MVP] Stage 1/4: 分析 + 前置探索 ...")
    _write_text(layout.llm1_system_prompt, client.load_stage_system_prompt("analyst").strip() + "\n")
    analyst = stage_analyst(client, requirement=requirement, out_dir=layout.llm1_dir)
    analysis, problem_solving, drawing_brief = _split_analyst_payload(analyst)
    print("[MVP] Stage 2/4: Scene 拆分规划 ...")
    _write_text(layout.llm2_system_prompt, client.load_stage_system_prompt("scene_planner").strip() + "\n")
    plan = stage_scene_plan(
        client,
        requirement=requirement,
        analysis=analysis,
        problem_solving=problem_solving,
        out_dir=layout.llm2_dir,
    )
    print("[MVP] Stage 3/4: 逐 Scene 设计（分镜稿） ...")
    _write_text(layout.llm3_system_prompt, client.load_stage_system_prompt("scene_designer").strip() + "\n")
    scene_designs = stage_scene_designs(
        client,
        requirement=requirement,
        drawing_brief=drawing_brief,
        plan=plan,
        out_dir=layout.llm3_dir,
    )
    print(f"[MVP] 已输出: {layout.stage3_json}")
    print("[MVP] Stage 4/4: 单文件代码生成（scene.py） ...")
    class_name, code = stage_codegen_video(
        client,
        stage1_problem_solving=problem_solving,
        stage1_drawing_brief=drawing_brief,
        plan=plan,
        scene_designs=scene_designs,
        out_dir=layout.llm4_dir,
    )

    py_file = layout.llm4_scene_py
    _write_text(py_file, code)
    # 导出到 run_dir 根目录，方便直接运行
    _write_text(layout.exported_scene_py, code)
    _write_text(
        layout.stage4_meta,
        json.dumps(
            {
                "class_name": class_name,
                "codegen_mode": "split_llm4",
                "sub_stages": ["framework", "scene", "motion", "assemble"],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    print(f"[MVP] 已生成: {py_file}（class_name={class_name}）")

    if args.no_render:
        return 0

    print("[MVP] 开始执行：渲染失败驱动修复循环（LLM4A-D -> scene.py -> manim -> LLM5 -> 重试）")
    class_name, ok, mp4_path, last_err, _last_attempt = stage_render_fix_loop(
        client,
        class_name=class_name,
        py_file=py_file,
        layout=layout,
        quality=args.quality,
        render_timeout_s=int(args.render_timeout_s),
        max_fix_rounds=int(args.max_fix_rounds),
    )
    if ok:
        print(f"[MVP] 渲染成功 -> {mp4_path}")
        return 0

    print("[MVP] 渲染失败（达到最大修复轮数）")
    _write_text(run_dir / "FAILED.txt", f"渲染失败：达到最大修复轮数 {args.max_fix_rounds}\n\n{last_err}")
    return 5


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        raise
