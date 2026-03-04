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
from typing import Any, Literal

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
    from pipeline.run_layout import RunLayout  # noqa: E402
    from pipeline.rendering import (  # noqa: E402
        detect_scene_classes,
        render_scene,
    )
else:
    from pipeline.codegen_contract import build_codegen_interface_contract  # noqa: E402
    from pipeline.config import ERROR_DIR, PROMPTS_DIR, RUNS_DIR  # noqa: E402
    from pipeline.llm_client import LLMClient, LLMStage  # noqa: E402
    from pipeline.run_layout import RunLayout  # noqa: E402
    from pipeline.rendering import (  # noqa: E402
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


def load_stage35_layouts(
    *,
    layout: RunLayout,
    scene_designs: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if layout.stage35_json.exists():
        return _load_json(layout.stage35_json)

    fallback_designs = scene_designs or (_load_json(layout.stage3_json) if layout.stage3_json.exists() else {"video_title": "", "scenes": []})
    fallback_scenes: list[dict[str, Any]] = []
    for item in fallback_designs.get("scenes") or []:
        if not isinstance(item, dict):
            continue
        fallback_scenes.append(
            {
                "scene_id": str(item.get("scene_id") or "").strip(),
                "class_name": str(item.get("class_name") or "").strip(),
                "layout_prompt": str(item.get("layout_prompt") or "").strip(),
                "layout_contract": _normalize_layout_contract(item.get("layout_contract")),
            }
        )
    return {
        "video_title": str(fallback_designs.get("video_title") or "").strip(),
        "scenes": fallback_scenes,
    }


def _dump_context_text(value: Any) -> str:
    try:
        return json.dumps(value, ensure_ascii=False)
    except Exception:  # noqa: BLE001
        return str(value)


def _contains_any(text: str, keywords: list[str]) -> bool:
    haystack = text.lower()
    return any(keyword.lower() in haystack for keyword in keywords)


def _infer_llm4e_component_groups(
    *,
    stage1_problem_solving: dict[str, Any],
    stage1_drawing_brief: dict[str, Any],
    plan: dict[str, Any],
    scene_designs: dict[str, Any],
    scene_layouts: dict[str, Any] | None,
) -> list[str]:
    context_text = "\n".join(
        [
            _dump_context_text(stage1_problem_solving),
            _dump_context_text(stage1_drawing_brief),
            _dump_context_text(plan),
            _dump_context_text(scene_designs),
            _dump_context_text(scene_layouts or {}),
        ]
    )

    groups = ["primitives"]

    mechanics_keywords = [
        "力学",
        "木板",
        "物块",
        "小车",
        "滑轮",
        "绳",
        "弹簧",
        "杆",
        "斜面",
        "轨道",
        "摩擦",
        "block",
        "cart",
        "pulley",
        "rope",
        "spring",
        "rod",
        "track",
        "friction",
    ]
    electricity_keywords = [
        "电路",
        "电流",
        "电压",
        "电阻",
        "电容",
        "电源",
        "开关",
        "灯泡",
        "滑动变阻器",
        "电表",
        "安培",
        "伏特",
        "resistor",
        "battery",
        "switch",
        "bulb",
        "capacitor",
        "ammeter",
        "voltmeter",
        "rheostat",
    ]
    electromagnetism_keywords = [
        "电磁",
        "磁场",
        "电场",
        "带电粒子",
        "粒子",
        "磁感应强度",
        "洛伦兹",
        "回旋",
        "particle",
        "magnetic",
        "electric field",
        "electromagnetism",
        "field_cross",
        "inductor",
    ]

    if _contains_any(context_text, mechanics_keywords):
        groups.append("mechanics")
    if _contains_any(context_text, electricity_keywords):
        groups.append("electricity")
    if _contains_any(context_text, electromagnetism_keywords):
        groups.append("electromagnetism")

    seen: set[str] = set()
    ordered: list[str] = []
    for item in groups:
        if item not in seen:
            ordered.append(item)
            seen.add(item)
    return ordered


def _load_llm4e_component_sources(component_groups: list[str]) -> tuple[str, list[str]]:
    components_root = PROMPTS_DIR / "llm4e_batch_codegen" / "references" / "components"
    sections: list[str] = []
    used_paths: list[str] = []

    for group in component_groups:
        group_dir = components_root / group
        if not group_dir.exists():
            continue
        files = [path for path in sorted(group_dir.glob("*.py")) if path.is_file() and path.name != "__init__.py"]
        if not files:
            continue

        rel_group = group_dir.relative_to(PROMPTS_DIR)
        section_parts = [f"# 组件源码参考：{rel_group.as_posix()}"]
        for path in files:
            rel_path = path.relative_to(PROMPTS_DIR).as_posix()
            used_paths.append(rel_path)
            section_parts.append(f"## {rel_path}\n```python\n{path.read_text(encoding='utf-8').strip()}\n```")
        sections.append("\n\n".join(section_parts).strip())

    merged = "\n\n".join(part for part in sections if part.strip()).strip()
    if not merged:
        return "", used_paths
    return merged + "\n", used_paths


def _load_llm4e_domain_references(component_groups: list[str]) -> tuple[str, list[str]]:
    refs_root = PROMPTS_DIR / "llm4e_batch_codegen" / "references"
    mapping = {
        "mechanics": refs_root / "mechanics_reference.md",
        "electromagnetism": refs_root / "electromagnetism_reference.md",
    }

    sections: list[str] = []
    used_paths: list[str] = []
    for group in component_groups:
        ref_path = mapping.get(group)
        if ref_path is None or not ref_path.exists():
            continue
        used_paths.append(ref_path.relative_to(PROMPTS_DIR).as_posix())
        sections.append(ref_path.read_text(encoding="utf-8").strip())

    merged = "\n\n".join(part for part in sections if part.strip()).strip()
    if not merged:
        return "", used_paths
    return merged + "\n", used_paths


def _build_llm4e_system_prompt(
    client: LLMClient,
    *,
    stage1_problem_solving: dict[str, Any],
    stage1_drawing_brief: dict[str, Any],
    plan: dict[str, Any],
    scene_designs: dict[str, Any],
    scene_layouts: dict[str, Any] | None,
) -> tuple[str, list[str], list[str]]:
    base_system = client.load_stage_system_prompt("codegen_bundle").strip()
    component_groups = _infer_llm4e_component_groups(
        stage1_problem_solving=stage1_problem_solving,
        stage1_drawing_brief=stage1_drawing_brief,
        plan=plan,
        scene_designs=scene_designs,
        scene_layouts=scene_layouts,
    )
    domain_references, domain_ref_paths = _load_llm4e_domain_references(component_groups)
    component_sources, used_paths = _load_llm4e_component_sources(component_groups)
    extras: list[str] = []
    if domain_references:
        extras.append(domain_references.strip())
    if component_sources:
        extras.append(
            (
                "以下组件源码仅作为参考实现与接口示例。优先复用其中稳定写法；如果运行时不确定可直接实例化，"
                "则退回基础 Manim 图元实现。\n\n"
                f"{component_sources.strip()}"
            ).strip()
        )

    if not extras:
        return base_system + "\n", component_groups, domain_ref_paths + used_paths

    merged = f"{base_system}\n\n" + "\n\n".join(extras)
    return merged.strip() + "\n", component_groups, domain_ref_paths + used_paths


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


def _normalize_codegen_bundle_payload(
    data: dict[str, Any],
    *,
    interface_contract: dict[str, Any],
) -> dict[str, Any]:
    raw_scenes = data.get("scenes") if isinstance(data.get("scenes"), list) else []
    if not isinstance(raw_scenes, list):
        raw_scenes = []
    raw_by_id = {
        str(item.get("scene_id") or "").strip(): item
        for item in raw_scenes
        if isinstance(item, dict) and str(item.get("scene_id") or "").strip()
    }

    normalized_scenes: list[dict[str, Any]] = []
    for idx, scene_contract in enumerate(interface_contract.get("scenes") or [], start=1):
        if not isinstance(scene_contract, dict):
            continue
        scene_id = str(scene_contract.get("scene_id") or "").strip() or f"scene_{idx:02d}"
        expected_scene = str(scene_contract.get("scene_method_name") or "").strip()
        expected_motion = str(scene_contract.get("motion_method_name") or "").strip()

        raw_scene = raw_by_id.get(scene_id)
        if raw_scene is None and idx - 1 < len(raw_scenes) and isinstance(raw_scenes[idx - 1], dict):
            raw_scene = raw_scenes[idx - 1]
        if not isinstance(raw_scene, dict):
            raw_scene = {}

        scene_method = str(raw_scene.get("scene_method") or "").strip()
        motion_method = str(raw_scene.get("motion_method") or "").strip()
        if not scene_method:
            raise RuntimeError(f"Claude batch codegen 缺少 {scene_id} 的 scene_method")
        if not motion_method:
            motion_method = _make_motion_stub(expected_motion).strip()

        normalized_scenes.append(
            {
                "scene_id": scene_id,
                "scene_method_name": expected_scene,
                "motion_method_name": expected_motion,
                "scene_method": scene_method,
                "motion_method": motion_method,
            }
        )

    return {
        "class_name": str(data.get("class_name") or interface_contract.get("preferred_class_name") or "MainScene").strip() or "MainScene",
        "scenes": normalized_scenes,
    }


def _write_codegen_bundle_fragments(
    *,
    out_dir: Path,
    bundle_payload: dict[str, Any],
) -> None:
    for item in bundle_payload.get("scenes") or []:
        if not isinstance(item, dict):
            continue
        scene_id = str(item.get("scene_id") or "").strip()
        scene_method_name = str(item.get("scene_method_name") or "").strip()
        motion_method_name = str(item.get("motion_method_name") or "").strip()

        scene_dir = out_dir / "scenes" / scene_id
        motion_dir = out_dir / "motion" / scene_id
        scene_fragment = _normalize_manim_ce_api(_extract_python_code(str(item.get("scene_method") or ""))).strip() + "\n"
        motion_fragment = _normalize_manim_ce_api(_extract_python_code(str(item.get("motion_method") or ""))).strip() + "\n"

        _write_text(scene_dir / "scene_method_raw.txt", str(item.get("scene_method") or "").strip() + "\n")
        _write_text(motion_dir / "motion_raw.txt", str(item.get("motion_method") or "").strip() + "\n")

        validated_scene = _extract_method_fragment(
            scene_fragment,
            expected_name=scene_method_name,
            fragment_label=f"batch scene fragment {scene_id}",
        )
        validated_motion = _extract_method_fragment(
            motion_fragment,
            expected_name=motion_method_name,
            fragment_label=f"batch motion fragment {scene_id}",
            allow_stub=True,
        )

        _write_text(scene_dir / "scene_method.py", validated_scene)
        _write_text(motion_dir / "motion_method.py", validated_motion)


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
                "anchor": str(item.get("anchor") or "").strip(),
                "placement": str(item.get("placement") or "").strip(),
                "stack_order": item.get("stack_order"),
                "relative_to": str(item.get("relative_to") or "").strip(),
                "avoid_overlap_with": _clean_str_list(item.get("avoid_overlap_with")),
            }
        )

    raw_step_layouts = layout.get("step_layouts")
    if not isinstance(raw_step_layouts, list):
        raw_step_layouts = layout.get("step_visibility") if isinstance(layout.get("step_visibility"), list) else []

    step_layouts: list[dict[str, Any]] = []
    for idx, item in enumerate(raw_step_layouts or [], start=1):
        if not isinstance(item, dict):
            continue
        raw_zone_overrides = item.get("zone_overrides") if isinstance(item.get("zone_overrides"), dict) else {}
        zone_overrides = {
            str(key).strip(): str(value).strip()
            for key, value in raw_zone_overrides.items()
            if str(key).strip() and str(value).strip()
        }
        step_layouts.append(
            {
                "step_id": str(item.get("step_id") or item.get("step") or f"step_{idx:02d}").strip() or f"step_{idx:02d}",
                "layout_objects": _clean_str_list(item.get("layout_objects") or item.get("active_objects")),
                "hidden_objects": _clean_str_list(item.get("hidden_objects")),
                "focus_objects": _clean_str_list(item.get("focus_objects")),
                "zone_overrides": zone_overrides,
            }
        )

    return {
        "version": str(layout.get("version") or "v2").strip() or "v2",
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
        "step_layouts": step_layouts,
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

    for item in layout.get("step_layouts") if isinstance(layout.get("step_layouts"), list) else []:
        if not isinstance(item, dict):
            continue
        overrides = item.get("zone_overrides") if isinstance(item.get("zone_overrides"), dict) else {}
        if subtitle_zone_id in overrides or "subtitle_zone" in overrides or "subtitle" in overrides:
            raise ValueError(f"{scene_id}: step_layouts may not override subtitle zone.")

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
    current_scene = dict(scene or {})
    current_scene.pop("layout_prompt", None)
    return (
        "[用户需求]\n"
        f"{requirement.strip()}\n\n"
        "[画图提示 JSON]\n"
        f"{json.dumps(drawing_brief, ensure_ascii=False, indent=2)}\n\n"
        "[上一 Scene 摘要]\n"
        f"{json.dumps(_scene_brief(prev_scene or {}), ensure_ascii=False, indent=2)}\n\n"
        "[当前 Scene]\n"
        f"{json.dumps(current_scene, ensure_ascii=False, indent=2)}\n\n"
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
        payload.pop("layout_prompt", None)
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


def build_scene_layouts_batch_user_prompt(
    *,
    requirement: str,
    drawing_brief: dict[str, Any],
    plan: dict[str, Any],
    scene_designs: dict[str, Any],
) -> str:
    scenes = plan.get("scenes") or []
    if not isinstance(scenes, list):
        scenes = []

    design_map = {
        str(item.get("scene_id") or "").strip(): item
        for item in (scene_designs.get("scenes") or [])
        if isinstance(item, dict) and str(item.get("scene_id") or "").strip()
    }

    scene_payload: list[dict[str, Any]] = []
    for scene in scenes:
        if not isinstance(scene, dict):
            continue
        sid = str(scene.get("scene_id") or "").strip()
        scene_payload.append(
            {
                "scene_plan": scene,
                "scene_brief": _scene_brief(scene),
                "scene_design": design_map.get(sid, {}),
            }
        )

    return (
        "[用户需求]\n"
        f"{requirement.strip()}\n\n"
        "[画图提示 JSON]\n"
        f"{json.dumps(drawing_brief, ensure_ascii=False, indent=2)}\n\n"
        "[整片 Scene 规划与对应设计稿]\n"
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
        "motion_contract",
    }
    return {key: value for key, value in payload.items() if key in allowed_keys}


def _normalize_scene_layout_payload(
    data: dict[str, Any],
    *,
    scene: dict[str, Any],
    scene_design: dict[str, Any],
) -> dict[str, Any]:
    payload = dict(data or {})
    layout_contract = _normalize_layout_contract(payload.get("layout_contract"))
    if not layout_contract.get("zones"):
        layout_contract = _normalize_layout_contract(scene_design.get("layout_contract"))

    normalized = {
        "scene_id": str(scene.get("scene_id") or payload.get("scene_id") or "").strip(),
        "class_name": str(scene.get("class_name") or payload.get("class_name") or "").strip(),
        "layout_prompt": str(payload.get("layout_prompt") or "").strip(),
        "layout_contract": layout_contract,
    }
    return normalized


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
        _reset_dir(layout.llm35_dir)
    elif from_stage == 35:
        _reset_dir(layout.llm35_dir)
    if from_stage <= 4:
        _reset_dir(layout.llm4_dir)
        _remove_path(layout.exported_scene_py)
    if from_stage <= 5:
        _reset_dir(layout.llm5_dir)
        _reset_dir(layout.render_dir)
        _remove_path(layout.exported_final_mp4)

    _remove_path(layout.run_dir / "FAILED.txt")


def build_client(
    *,
    llm1_provider: Literal["zhipu", "anthropic", "kimi"] = "zhipu",
    llm35_provider: Literal["zhipu", "anthropic", "kimi"] = "zhipu",
    llm4_provider: Literal["zhipu", "anthropic", "kimi"] = "zhipu",
    llm5_provider: Literal["zhipu", "anthropic", "kimi"] | None = None,
) -> LLMClient:
    # 复用 MVP/configs/llm.yaml 里的 stage 采样 profile
    llm5_provider = llm4_provider if llm5_provider is None else llm5_provider
    stage_map = {
        "analyst": LLMStage(
            name="analyst",
            provider=llm1_provider,
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
        "layout_designer": LLMStage(
            name="layout_designer",
            provider=llm35_provider,
            profile_stage="layout_designer",
            prompt_bundle="llm35_layout_designer",
        ),
        "codegen_bundle": LLMStage(
            name="codegen_bundle",
            provider=llm4_provider,
            profile_stage="codegen_bundle",
            prompt_bundle="llm4e_batch_codegen",
        ),
        "fixer": LLMStage(
            name="fixer",
            provider=llm5_provider,
            profile_stage="fixer",
            prompt_bundle="llm5_fixer",
        ),
    }
    return LLMClient(prompts_dir=PROMPTS_DIR, stage_map=stage_map)


