from __future__ import annotations

import argparse
import ast
import importlib.util
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from types import ModuleType
from typing import Any

from pipeline.env import load_dotenv
from pipeline.json_utils import load_json_from_llm
from pipeline.llm.types import ChatMessage
from pipeline.llm.zhipu import chat_completion, load_zhipu_config, load_zhipu_stage_config
from pipeline.llm_continuation import continue_json_output
from pipeline.prompting import compose_prompt
from schema.scene_codegen_models import SceneCodegenPlan
from schema.scene_plan_models import ScenePlan


_CODE_KEY_RE = re.compile(r"^[a-z][a-z0-9_]{1,63}$")
_PYTHON_BLOCK_RE = re.compile(r"```(?:python)?\s*(.*?)```", re.IGNORECASE | re.DOTALL)

_BANNED_IMPORT_ROOTS = {
    "os",
    "sys",
    "pathlib",
    "subprocess",
    "shutil",
    "socket",
    "urllib",
    "requests",
    "http",
    "ftplib",
    "glob",
}
_BANNED_CALL_NAMES = {
    "eval",
    "exec",
    "open",
    "compile",
    "__import__",
    "input",
    "breakpoint",
}
_BANNED_CALL_ROOTS = {"os", "subprocess", "pathlib", "shutil", "socket", "urllib", "requests"}
_CODEGEN_REQUEST_KIND_ALLOWED = {"new_component", "special_motion", "complex_effect", "hybrid", "custom"}
_CODEGEN_REQUEST_SCOPE_ALLOWED = {"object", "motion", "effect", "hybrid"}
_STATE_DRIVER_MODEL_KINDS = {"ballistic_2d", "uniform_circular_2d", "sampled_path_2d"}


def _write_continuation_chunks(case_dir: Path, stem: str, chunks: list[str]) -> None:
    for idx, chunk in enumerate(chunks, start=1):
        (case_dir / f"{stem}_{idx}.txt").write_text(chunk.strip() + "\n", encoding="utf-8")


def _render_error_lines(errors: list[str], *, limit: int = 60) -> str:
    if not errors:
        return "(no validation errors)"
    lines = [f"- {err}" for err in errors[:limit]]
    if len(errors) > limit:
        lines.append(f"- ... and {len(errors) - limit} more errors")
    return "\n".join(lines)


def _load_optional_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return None
    if isinstance(parsed, dict):
        return parsed
    return None


def _normalize_codegen_request(raw: Any) -> dict[str, Any] | None:
    if not isinstance(raw, dict):
        return None

    enabled_raw = raw.get("enabled")
    if not isinstance(enabled_raw, bool):
        return None

    marker: dict[str, Any] = {"enabled": bool(enabled_raw)}

    kind_raw = raw.get("kind_hint")
    if isinstance(kind_raw, str) and kind_raw.strip():
        kind = kind_raw.strip().lower()
        if kind in _CODEGEN_REQUEST_KIND_ALLOWED:
            marker["kind_hint"] = kind

    scope_raw = raw.get("scope")
    if isinstance(scope_raw, str) and scope_raw.strip():
        scope = scope_raw.strip().lower()
        if scope in _CODEGEN_REQUEST_SCOPE_ALLOWED:
            marker["scope"] = scope

    intent_raw = raw.get("intent")
    if isinstance(intent_raw, str) and intent_raw.strip():
        marker["intent"] = intent_raw.strip()

    return marker


def _collect_custom_targets(
    plan: ScenePlan,
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]], str]:
    all_targets: dict[str, dict[str, Any]] = {}
    marked_targets: dict[str, dict[str, Any]] = {}
    markers: dict[str, dict[str, Any]] = {}

    for object_id, spec in plan.objects.items():
        if spec.type != "CustomObject":
            continue
        params = dict(spec.params or {})
        all_targets[object_id] = params
        marker = _normalize_codegen_request(params.get("codegen_request"))
        if marker is None:
            continue
        markers[object_id] = marker
        if bool(marker.get("enabled")):
            marked_targets[object_id] = params

    # Backward compatibility:
    # if no explicit enabled marker is found, keep old behavior (all CustomObject targets).
    if marked_targets:
        return marked_targets, markers, "marked_only"
    return all_targets, markers, "all_custom_objects"


def _collect_custom_targets_from_semantic(
    semantic_data: dict[str, Any],
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]], str]:
    all_targets: dict[str, dict[str, Any]] = {}
    marked_targets: dict[str, dict[str, Any]] = {}
    markers: dict[str, dict[str, Any]] = {}

    scenes = semantic_data.get("scenes")
    if not isinstance(scenes, list):
        return {}, {}, "all_custom_objects"

    for scene in scenes:
        if not isinstance(scene, dict):
            continue
        objects = scene.get("objects")
        if not isinstance(objects, list):
            continue
        for item in objects:
            if not isinstance(item, dict):
                continue
            if str(item.get("type", "")).strip() != "CustomObject":
                continue
            object_id = str(item.get("id", "")).strip()
            if not object_id:
                continue
            params_raw = item.get("params")
            params = dict(params_raw) if isinstance(params_raw, dict) else {}
            all_targets[object_id] = params
            marker = _normalize_codegen_request(params.get("codegen_request"))
            if marker is None:
                continue
            markers[object_id] = marker
            if bool(marker.get("enabled")):
                marked_targets[object_id] = params

    if marked_targets:
        return marked_targets, markers, "marked_only"
    return all_targets, markers, "all_custom_objects"


def _scene_usage_for_targets(plan_data: dict[str, Any], target_ids: set[str]) -> dict[str, list[str]]:
    scenes = plan_data.get("scenes")
    if not isinstance(scenes, list):
        return {}

    usage: dict[str, list[str]] = {}
    for scene in scenes:
        if not isinstance(scene, dict):
            continue
        scene_id = str(scene.get("id", "")).strip()
        if not scene_id:
            continue

        hit: set[str] = set()
        layout = scene.get("layout")
        if isinstance(layout, dict):
            slots = layout.get("slots")
            if isinstance(slots, dict):
                for object_id in slots.values():
                    oid = str(object_id).strip()
                    if oid in target_ids:
                        hit.add(oid)
            placements = layout.get("placements")
            if isinstance(placements, dict):
                for object_id in placements.keys():
                    oid = str(object_id).strip()
                    if oid in target_ids:
                        hit.add(oid)

        actions = scene.get("actions")
        if isinstance(actions, list):
            for action in actions:
                if not isinstance(action, dict):
                    continue
                raw_targets = action.get("targets")
                if isinstance(raw_targets, list):
                    for object_id in raw_targets:
                        oid = str(object_id).strip()
                        if oid in target_ids:
                            hit.add(oid)
                for key in ("src", "dst"):
                    object_id = action.get(key)
                    oid = str(object_id).strip() if isinstance(object_id, str) else ""
                    if oid in target_ids:
                        hit.add(oid)

        keep = scene.get("keep")
        if isinstance(keep, list):
            for object_id in keep:
                oid = str(object_id).strip()
                if oid in target_ids:
                    hit.add(oid)

        if hit:
            usage[scene_id] = sorted(hit)
    return usage


def _scene_usage_for_targets_in_semantic(semantic_data: dict[str, Any], target_ids: set[str]) -> dict[str, list[str]]:
    scenes = semantic_data.get("scenes")
    if not isinstance(scenes, list):
        return {}

    usage: dict[str, list[str]] = {}
    for scene in scenes:
        if not isinstance(scene, dict):
            continue
        scene_id = str(scene.get("id", "")).strip()
        if not scene_id:
            continue
        objects = scene.get("objects")
        if not isinstance(objects, list):
            continue
        hit: list[str] = []
        for item in objects:
            if not isinstance(item, dict):
                continue
            oid = str(item.get("id", "")).strip()
            if oid and oid in target_ids:
                hit.append(oid)
        if hit:
            usage[scene_id] = sorted(set(hit))
    return usage


def _semantic_hints_by_object(semantic_data: dict[str, Any] | None, target_ids: set[str]) -> dict[str, list[str]]:
    if not isinstance(semantic_data, dict):
        return {}

    scenes = semantic_data.get("scenes")
    if not isinstance(scenes, list):
        return {}

    result: dict[str, list[str]] = {object_id: [] for object_id in sorted(target_ids)}
    for scene in scenes:
        if not isinstance(scene, dict):
            continue
        scene_id = str(scene.get("id", "")).strip()
        if not scene_id:
            continue
        object_set: set[str] = set()
        objects = scene.get("objects")
        if isinstance(objects, list):
            for item in objects:
                if not isinstance(item, dict):
                    continue
                object_id = str(item.get("id", "")).strip()
                if object_id in target_ids:
                    object_set.add(object_id)

        if not object_set:
            continue

        intent = str(scene.get("intent", "")).strip()
        if intent:
            for object_id in object_set:
                result[object_id].append(f"[{scene_id}] intent: {intent}")

        storyboard = scene.get("narrative_storyboard")
        if isinstance(storyboard, dict):
            intro = str(storyboard.get("intro", "")).strip()
            if intro:
                for object_id in object_set:
                    result[object_id].append(f"[{scene_id}] intro: {intro}")

            steps = storyboard.get("animation_steps")
            if isinstance(steps, list):
                for step in steps:
                    if not isinstance(step, dict):
                        continue
                    desc = str(step.get("description", "")).strip()
                    if not desc:
                        continue
                    targets = step.get("targets")
                    step_targets: set[str] = set()
                    if isinstance(targets, list):
                        for value in targets:
                            object_id = str(value).strip()
                            if object_id in target_ids:
                                step_targets.add(object_id)
                    for object_id in (step_targets or object_set):
                        result[object_id].append(f"[{scene_id}] step: {desc}")

    compact: dict[str, list[str]] = {}
    for object_id, hints in result.items():
        filtered: list[str] = []
        seen: set[str] = set()
        for hint in hints:
            if hint in seen:
                continue
            seen.add(hint)
            filtered.append(hint)
            if len(filtered) >= 10:
                break
        if filtered:
            compact[object_id] = filtered
    return compact


def _build_manifest_user_payload(
    *,
    problem: str,
    custom_targets: dict[str, dict[str, Any]],
    codegen_markers: dict[str, dict[str, Any]],
    selection_mode: str,
    scene_usage: dict[str, list[str]],
    semantic_hints: dict[str, list[str]],
) -> str:
    dsl_contract = {
        "dsl_version": "1.0",
        "kind": "new_component | special_motion | complex_effect | hybrid | custom",
        "geometry": {"...": "几何/构造参数"},
        "style": {"...": "颜色/线宽/透明度等样式参数"},
        "motion": {
            "...": "连续运动与时序参数",
            "driver": {
                "type": "state_driver",
                "target_object_id": "目标 CompositeObject 的 object_id",
                "motion_id": "m_xxx",
                "part_id": "目标 graph.parts[].id",
                "args": {
                    "mode": "model",
                    "param_key": "tau",
                    "orient_mode": "fixed | velocity_tangent",
                    "model": {
                        "kind": "ballistic_2d | uniform_circular_2d | sampled_path_2d",
                        "params": {"...": "对应 kind 参数"},
                    },
                },
                "timeline": [{"t": 0.0, "tau": 0.0}, {"t": 4.0, "tau": 1.0}],
            },
        },
        "effects": {"...": "形变或特效参数（可空对象）"},
        "meta": {"...": "可选元信息（可空对象）"},
    }
    return "\n".join(
        [
            "题目：",
            problem.strip() or "(empty)",
            "",
            "必须生成代码的 CustomObject 目标（object_id -> 当前 params）：",
            json.dumps(custom_targets, ensure_ascii=False, indent=2),
            "",
            "目标选择模式：",
            selection_mode,
            "",
            "scene_plan 中的 codegen_request 标记（可为空）：",
            json.dumps(codegen_markers, ensure_ascii=False, indent=2),
            "",
            "这些对象在 scene_plan 中的出现分布：",
            json.dumps(scene_usage, ensure_ascii=False, indent=2),
            "",
            "来自 scene_semantic 的叙事/动作提示（可为空）：",
            json.dumps(semantic_hints, ensure_ascii=False, indent=2),
            "",
            "spec DSL 合同（必须严格遵守键名）：",
            json.dumps(dsl_contract, ensure_ascii=False, indent=2),
            "",
            "输出要求：",
            "- 仅输出 scene_codegen.json（严格 JSON 对象）。",
            "- 每个目标 object_id 必须且只能出现一次。",
            "- code_key 只能是小写字母开头的 snake_case（示例：orbit_probe）。",
            "- spec 必须使用 DSL 骨架，禁止自由散乱顶层键。",
            "- spec 禁止放 Python 代码或 markdown。",
            "- 若该 CustomObject 需要把复杂运动回填到 scene_plan，请在 spec.motion.driver 提供完整 state_driver 合同。",
            "- spec.motion.driver.target_object_id 必须指向真实 CompositeObject（不是 CustomObject）。",
            "- spec.motion.driver.args.model.kind 只允许 ballistic_2d / uniform_circular_2d / sampled_path_2d。",
            "- motion_span_s: 有连续运动给正数秒，无连续运动给 null。",
            "- 禁止输出 markdown。",
        ]
    )


def _build_manifest_repair_payload(
    *,
    problem: str,
    custom_targets: dict[str, dict[str, Any]],
    codegen_markers: dict[str, dict[str, Any]],
    selection_mode: str,
    scene_usage: dict[str, list[str]],
    semantic_hints: dict[str, list[str]],
    raw_content: str,
    errors: list[str],
    round_index: int,
) -> str:
    return "\n".join(
        [
            f"这是第 {round_index} 轮修复。请最小修改并修复 scene_codegen.json。",
            "只输出 JSON。",
            "",
            "校验错误：",
            _render_error_lines(errors),
            "",
            "题目：",
            problem.strip() or "(empty)",
            "",
            "必须覆盖的 CustomObject 目标：",
            json.dumps(custom_targets, ensure_ascii=False, indent=2),
            "",
            "目标选择模式：",
            selection_mode,
            "",
            "scene_plan 中的 codegen_request 标记（可为空）：",
            json.dumps(codegen_markers, ensure_ascii=False, indent=2),
            "",
            "scene 分布：",
            json.dumps(scene_usage, ensure_ascii=False, indent=2),
            "",
            "叙事提示：",
            json.dumps(semantic_hints, ensure_ascii=False, indent=2),
            "",
            "当前错误内容：",
            raw_content.strip(),
            "",
            "硬约束：",
            "1) 只输出 scene_codegen.json。",
            "2) objects 里必须覆盖所有目标 object_id，且不能有额外 object_id。",
            "3) code_key 必须是 snake_case。",
            "4) spec 必须符合 DSL 骨架（dsl_version/kind/geometry/style/motion/effects/meta）。",
            "5) motion_span_s 只能是正数或 null。",
            "6) 若给出 spec.motion.driver，必须是可回填的 state_driver 合同。",
        ]
    )


def _parse_manifest_and_validate(
    content: str,
    *,
    target_ids: set[str],
) -> tuple[SceneCodegenPlan | None, list[str]]:
    try:
        data = load_json_from_llm(content)
    except Exception as exc:  # noqa: BLE001
        return None, [f"JSON parse failed: {exc}"]

    try:
        manifest = SceneCodegenPlan.model_validate(data)
    except Exception as exc:  # noqa: BLE001
        return None, [f"scene_codegen schema invalid: {exc}"]

    errors: list[str] = []
    object_ids = {item.object_id for item in manifest.objects}
    missing = sorted(target_ids - object_ids)
    extra = sorted(object_ids - target_ids)
    if missing:
        errors.append(f"Missing object_id in scene_codegen.objects: {missing}")
    if extra:
        errors.append(f"Unexpected object_id in scene_codegen.objects: {extra}")

    for item in manifest.objects:
        if not _CODE_KEY_RE.match(item.code_key):
            errors.append(
                f"object_id='{item.object_id}' has invalid code_key='{item.code_key}' (must be snake_case)"
            )

    if errors:
        return None, errors
    return manifest, []


def _extract_python_code(raw: str) -> str:
    text = str(raw or "").strip()
    if not text:
        return ""

    hit = _PYTHON_BLOCK_RE.search(text)
    if hit:
        return hit.group(1).strip()

    if text.startswith("```") and text.endswith("```"):
        lines = text.splitlines()
        if len(lines) >= 3:
            return "\n".join(lines[1:-1]).strip()
    return text


def _root_name(expr: ast.AST) -> str | None:
    node = expr
    while isinstance(node, ast.Attribute):
        node = node.value
    if isinstance(node, ast.Name):
        return node.id
    return None


def _validate_codegen_ast(code: str) -> list[str]:
    errors: list[str] = []
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return [f"Python syntax error: {exc}"]

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = str(alias.name).split(".", 1)[0]
                if root in _BANNED_IMPORT_ROOTS:
                    errors.append(f"Banned import: {alias.name} (line {node.lineno})")
        elif isinstance(node, ast.ImportFrom):
            module = str(node.module or "")
            root = module.split(".", 1)[0]
            if root in _BANNED_IMPORT_ROOTS:
                errors.append(f"Banned import-from: {module} (line {node.lineno})")
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                if node.func.id in _BANNED_CALL_NAMES:
                    errors.append(f"Banned function call: {node.func.id} (line {node.lineno})")
                if node.func.id == "ArrowTip":
                    errors.append(
                        "Forbidden arrow API: ArrowTip(...) is abstract. "
                        f"Use Arrow/CurvedArrow or Line(...).add_tip() (line {node.lineno})"
                    )
            else:
                root = _root_name(node.func)
                if root in _BANNED_CALL_ROOTS:
                    errors.append(f"Banned call root: {root} (line {node.lineno})")
                if isinstance(node.func, ast.Attribute) and node.func.attr == "add_tip":
                    owner_call = node.func.value
                    owner_ctor: str | None = None
                    if isinstance(owner_call, ast.Call):
                        ctor = owner_call.func
                        if isinstance(ctor, ast.Name):
                            owner_ctor = ctor.id
                        elif isinstance(ctor, ast.Attribute):
                            owner_ctor = _root_name(ctor)
                    if owner_ctor == "CubicBezier":
                        errors.append(
                            "Forbidden arrow API: CubicBezier(...).add_tip(...) is unsupported. "
                            f"Use CurvedArrow(...) or Line(...).add_tip() (line {node.lineno})"
                        )
    return errors


def _load_module_from_code(code: str, *, case_dir: Path) -> ModuleType:
    module_fd, module_path_raw = tempfile.mkstemp(
        prefix="_llm_codegen_validate_",
        suffix=".py",
        dir=str(case_dir),
    )
    module_path = Path(module_path_raw)
    try:
        with os.fdopen(module_fd, "w", encoding="utf-8") as fh:
            fh.write(code)
            if not code.endswith("\n"):
                fh.write("\n")

        module_name = f"_llm_codegen_validate_{abs(hash(str(module_path)))}"
        spec = importlib.util.spec_from_file_location(module_name, str(module_path))
        if spec is None or spec.loader is None:
            raise RuntimeError("Failed to create import spec for generated code")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        try:
            module_path.unlink(missing_ok=True)
        except Exception:  # noqa: BLE001
            pass


def _validate_codegen_runtime(code: str, manifest: SceneCodegenPlan, *, case_dir: Path) -> list[str]:
    errors = _validate_codegen_ast(code)
    if errors:
        return errors

    try:
        module = _load_module_from_code(code, case_dir=case_dir)
    except Exception as exc:  # noqa: BLE001
        return [f"Failed to import generated module: {exc}"]

    builders = getattr(module, "BUILDERS", None)
    if not isinstance(builders, dict):
        return ["Generated code must define BUILDERS as a dict"]

    updaters_raw = getattr(module, "UPDATERS", {})
    if updaters_raw is None:
        updaters_raw = {}
    if not isinstance(updaters_raw, dict):
        return ["Generated code UPDATERS must be a dict when provided"]

    try:
        from manim import Mobject
    except Exception as exc:  # noqa: BLE001
        return [f"Failed to import manim.Mobject for runtime checks: {exc}"]

    runtime_errors: list[str] = []
    for item in manifest.objects:
        key = item.code_key
        builder = builders.get(key)
        if builder is None:
            runtime_errors.append(f"BUILDERS missing key: {key}")
            continue
        if not callable(builder):
            runtime_errors.append(f"BUILDERS['{key}'] is not callable")
            continue

        spec = item.spec.model_dump(mode="json")
        try:
            mobj = builder(spec)
        except Exception as exc:  # noqa: BLE001
            runtime_errors.append(f"Builder '{key}' raised exception: {exc}")
            continue

        if not isinstance(mobj, Mobject):
            runtime_errors.append(f"Builder '{key}' must return Manim Mobject")
            continue

        updater = updaters_raw.get(key)
        if updater is None:
            continue
        if not callable(updater):
            runtime_errors.append(f"UPDATERS['{key}'] is not callable")
            continue

        t_value = float(item.motion_span_s or 0.5)
        try:
            updater(mobj, t_value, spec)
        except Exception as exc:  # noqa: BLE001
            runtime_errors.append(f"Updater '{key}' raised exception: {exc}")

    return runtime_errors


def _build_code_user_payload(
    *,
    problem: str,
    manifest: SceneCodegenPlan,
    semantic_hints: dict[str, list[str]],
    existing_code: str,
) -> str:
    existing_preview = existing_code.strip()
    if len(existing_preview) > 6000:
        existing_preview = existing_preview[:6000] + "\n# ... truncated ..."

    return "\n".join(
        [
            "题目：",
            problem.strip() or "(empty)",
            "",
            "scene_codegen.json：",
            json.dumps(manifest.model_dump(mode="json"), ensure_ascii=False, indent=2),
            "",
            "语义提示（对象 -> 叙事/动画提示）：",
            json.dumps(semantic_hints, ensure_ascii=False, indent=2),
            "",
            "如果有历史代码，参考如下（可重写）：",
            existing_preview or "(none)",
            "",
            "输出要求：",
            "- 输出完整 llm_codegen.py 纯 Python 代码，不要 markdown。",
            "- 必须定义 BUILDERS: dict[str, callable]。",
            "- 可选定义 UPDATERS: dict[str, callable]。",
            "- BUILDERS 必须覆盖 scene_codegen.json 中每个 code_key。",
            "- builder 签名: (spec: dict[str, Any]) -> Mobject。",
            "- updater 签名: (mobj: Mobject, t: float, spec: dict[str, Any]) -> None。",
            "- 仅使用 manim / math / numpy / typing 等安全库。",
            "- 禁止文件、网络、系统命令相关操作。",
            "- spec 使用 DSL，优先读取 spec['geometry'/'style'/'motion'/'effects'/'meta']。",
            "- 箭头 API 约束：优先 Arrow/CurvedArrow 或 Line(...).add_tip()；禁止 ArrowTip(...) 与 CubicBezier(...).add_tip(...)。",
        ]
    )


def _build_code_repair_payload(
    *,
    problem: str,
    manifest: SceneCodegenPlan,
    semantic_hints: dict[str, list[str]],
    raw_code: str,
    errors: list[str],
    round_index: int,
) -> str:
    return "\n".join(
        [
            f"这是第 {round_index} 轮代码修复。请最小改动修复 llm_codegen.py。",
            "仅输出完整 Python 代码，不要 markdown。",
            "",
            "校验错误：",
            _render_error_lines(errors),
            "",
            "题目：",
            problem.strip() or "(empty)",
            "",
            "scene_codegen.json：",
            json.dumps(manifest.model_dump(mode="json"), ensure_ascii=False, indent=2),
            "",
            "语义提示：",
            json.dumps(semantic_hints, ensure_ascii=False, indent=2),
            "",
            "当前错误代码：",
            raw_code.strip(),
            "",
            "硬约束：",
            "1) BUILDERS 必须包含所有 code_key。",
            "2) builder 必须返回 Mobject。",
            "3) 若提供 UPDATERS，必须可调用且不报错。",
            "4) 禁止 os/subprocess/pathlib/socket/urllib/requests/open/eval/exec。",
            "5) 按 DSL 读取 spec（geometry/style/motion/effects/meta）。",
            "6) 箭头相关禁止：ArrowTip(...)、CubicBezier(...).add_tip(...); 优先 Arrow/CurvedArrow 或 Line(...).add_tip()。",
        ]
    )
def _safe_float(value: Any) -> float | None:
    try:
        return float(value)
    except Exception:  # noqa: BLE001
        return None


def _extract_motion_driver_from_spec(spec: dict[str, Any]) -> dict[str, Any] | None:
    motion_cfg = spec.get("motion")
    if not isinstance(motion_cfg, dict):
        return None
    driver = motion_cfg.get("driver")
    if not isinstance(driver, dict):
        return None
    return json.loads(json.dumps(driver, ensure_ascii=False))


def _normalize_state_driver_payload(
    driver: dict[str, Any],
    *,
    context: str,
) -> tuple[dict[str, Any] | None, list[str]]:
    errors: list[str] = []

    driver_type = str(driver.get("type", "state_driver")).strip().lower()
    if driver_type != "state_driver":
        errors.append(f"{context}: spec.motion.driver.type must be 'state_driver'")

    target_object_id = str(driver.get("target_object_id", "")).strip()
    if not target_object_id:
        errors.append(f"{context}: spec.motion.driver.target_object_id is required")

    motion_id = str(driver.get("motion_id", "")).strip()
    if not motion_id:
        errors.append(f"{context}: spec.motion.driver.motion_id is required")

    part_id = str(driver.get("part_id", "")).strip()
    if not part_id:
        errors.append(f"{context}: spec.motion.driver.part_id is required")

    args_raw = driver.get("args")
    if not isinstance(args_raw, dict):
        errors.append(f"{context}: spec.motion.driver.args must be an object")
        args_raw = {}
    args = dict(args_raw)
    args["part_id"] = part_id

    mode = str(args.get("mode", "")).strip().lower()
    if mode != "model":
        errors.append(f"{context}: spec.motion.driver.args.mode must be 'model'")

    param_key = str(args.get("param_key", "")).strip()
    if param_key != "tau":
        errors.append(f"{context}: spec.motion.driver.args.param_key must be 'tau'")

    model = args.get("model")
    if not isinstance(model, dict):
        errors.append(f"{context}: spec.motion.driver.args.model must be an object")
        model = {}
    kind = str(model.get("kind", "")).strip().lower()
    if kind not in _STATE_DRIVER_MODEL_KINDS:
        allowed = ", ".join(sorted(_STATE_DRIVER_MODEL_KINDS))
        errors.append(f"{context}: spec.motion.driver.args.model.kind must be one of: {allowed}")

    params = model.get("params")
    if not isinstance(params, dict):
        errors.append(f"{context}: spec.motion.driver.args.model.params must be an object")
        params = {}

    timeline_raw = driver.get("timeline")
    timeline: list[dict[str, Any]] = []
    if not isinstance(timeline_raw, list) or len(timeline_raw) < 2:
        errors.append(f"{context}: spec.motion.driver.timeline must contain at least 2 keyframes")
    else:
        prev_t: float | None = None
        for index, point in enumerate(timeline_raw):
            if not isinstance(point, dict):
                errors.append(f"{context}: spec.motion.driver.timeline[{index}] must be an object")
                continue
            t_value = _safe_float(point.get("t"))
            tau_value = _safe_float(point.get("tau"))
            if t_value is None:
                errors.append(f"{context}: spec.motion.driver.timeline[{index}].t must be numeric")
                continue
            if tau_value is None:
                errors.append(f"{context}: spec.motion.driver.timeline[{index}].tau must be numeric")
                continue
            if prev_t is not None and t_value <= prev_t:
                errors.append(f"{context}: spec.motion.driver.timeline.t must be strictly increasing")
            prev_t = t_value
            timeline.append({"t": float(t_value), "tau": float(tau_value)})

    if kind == "sampled_path_2d":
        samples = params.get("samples")
        sample_taus: list[float] = []
        if not isinstance(samples, list) or len(samples) < 2:
            errors.append(f"{context}: sampled_path_2d requires params.samples with >= 2 points")
        else:
            prev_tau: float | None = None
            for index, sample in enumerate(samples):
                if not isinstance(sample, dict):
                    errors.append(f"{context}: params.samples[{index}] must be an object")
                    continue
                tau = _safe_float(sample.get("tau"))
                x = _safe_float(sample.get("x"))
                y = _safe_float(sample.get("y"))
                if tau is None or x is None or y is None:
                    errors.append(f"{context}: params.samples[{index}] requires numeric tau/x/y")
                    continue
                if tau < 0.0 or tau > 1.0:
                    errors.append(f"{context}: params.samples[{index}].tau must be in [0,1]")
                    continue
                if prev_tau is not None and tau <= prev_tau:
                    errors.append(f"{context}: params.samples.tau must be strictly increasing")
                    continue
                prev_tau = tau
                sample_taus.append(float(tau))
        if sample_taus and timeline:
            tau_min = sample_taus[0]
            tau_max = sample_taus[-1]
            for index, point in enumerate(timeline):
                tau_value = float(point["tau"])
                if tau_value < tau_min - 1e-9 or tau_value > tau_max + 1e-9:
                    errors.append(
                        f"{context}: timeline[{index}].tau {tau_value} outside samples range [{tau_min},{tau_max}]"
                    )
    elif kind == "ballistic_2d":
        for key in ("x0", "y0", "vx0", "vy0"):
            if _safe_float(params.get(key)) is None:
                errors.append(f"{context}: ballistic_2d requires numeric params.{key}")
    elif kind == "uniform_circular_2d":
        for key in ("cx", "cy", "r", "omega"):
            if _safe_float(params.get(key)) is None:
                errors.append(f"{context}: uniform_circular_2d requires numeric params.{key}")
        radius = _safe_float(params.get("r"))
        if radius is not None and radius <= 0.0:
            errors.append(f"{context}: uniform_circular_2d params.r must be > 0")

    if errors:
        return None, errors

    motion_payload = {
        "id": motion_id,
        "type": "state_driver",
        "args": args,
        "timeline": timeline,
    }
    return {"target_object_id": target_object_id, "motion": motion_payload}, []


def _apply_manifest_to_plan(
    plan_data: dict[str, Any],
    manifest: SceneCodegenPlan,
    *,
    code_file: str = "llm_codegen.py",
    return_errors: bool = False,
) -> dict[str, Any] | tuple[dict[str, Any], list[str]]:
    updated = json.loads(json.dumps(plan_data, ensure_ascii=False))
    objects = updated.get("objects")
    if not isinstance(objects, dict):
        base_error = ["scene_plan.objects must be an object"]
        return (updated, base_error) if return_errors else updated

    errors: list[str] = []

    for item in manifest.objects:
        obj = objects.get(item.object_id)
        if not isinstance(obj, dict):
            errors.append(f"scene_plan.objects['{item.object_id}'] missing")
            continue
        params = dict(obj.get("params") or {})
        spec_dict = item.spec.model_dump(mode="json")
        params["code_key"] = item.code_key
        params["spec"] = spec_dict
        params["code_file"] = str(code_file)
        if item.motion_span_s is not None:
            params["motion_span_s"] = float(item.motion_span_s)
        else:
            params.pop("motion_span_s", None)
        obj["params"] = params

        driver = _extract_motion_driver_from_spec(spec_dict)
        if driver is None:
            continue

        context = f"scene_codegen object_id='{item.object_id}'"
        normalized, driver_errors = _normalize_state_driver_payload(driver, context=context)
        if driver_errors:
            errors.extend(driver_errors)
            continue
        assert normalized is not None

        target_object_id = str(normalized["target_object_id"])
        target = objects.get(target_object_id)
        if not isinstance(target, dict):
            errors.append(f"{context}: target_object_id '{target_object_id}' not found in scene_plan.objects")
            continue
        target_type = str(target.get("type", "")).strip()
        if target_type != "CompositeObject":
            errors.append(f"{context}: target_object_id '{target_object_id}' must be CompositeObject")
            continue

        target_params = dict(target.get("params") or {})
        graph = target_params.get("graph")
        if not isinstance(graph, dict):
            errors.append(f"{context}: target CompositeObject '{target_object_id}' has no params.graph")
            continue

        parts = graph.get("parts")
        part_ids: set[str] = set()
        if isinstance(parts, list):
            for part in parts:
                if isinstance(part, dict):
                    part_id = str(part.get("id", "")).strip()
                    if part_id:
                        part_ids.add(part_id)
        motion_part_id = str(normalized["motion"]["args"].get("part_id", "")).strip()
        if motion_part_id not in part_ids:
            errors.append(
                f"{context}: part_id '{motion_part_id}' not found in target '{target_object_id}'.graph.parts"
            )
            continue

        motions_raw = graph.get("motions")
        motions = list(motions_raw) if isinstance(motions_raw, list) else []
        motion_payload = json.loads(json.dumps(normalized["motion"], ensure_ascii=False))
        motion_id = str(motion_payload.get("id", "")).strip()

        replaced = False
        for index, existing in enumerate(motions):
            if not isinstance(existing, dict):
                continue
            if str(existing.get("id", "")).strip() == motion_id:
                motions[index] = motion_payload
                replaced = True
                break
        if not replaced:
            motions.append(motion_payload)

        graph["motions"] = motions
        target_params["graph"] = graph
        target["params"] = target_params

    if return_errors:
        return updated, errors
    return updated


def main() -> int:
    parser = argparse.ArgumentParser(description="LLM-codegen: generate scene_codegen.json + llm_codegen.py")
    parser.add_argument("--case", default="cases/demo_001", help="Case directory, e.g. cases/demo_001")
    parser.add_argument("--plan", default=None, help="Optional scene_plan.json path (default: case/scene_plan.json)")
    parser.add_argument("--problem", default=None, help="Optional problem file path (default: case/problem.md)")
    parser.add_argument("--semantic", default=None, help="Optional scene_semantic.json path")
    parser.add_argument(
        "--targets-from",
        choices=("plan", "semantic"),
        default="plan",
        help="Where to collect CustomObject codegen targets from",
    )
    parser.add_argument(
        "--skip-apply-plan",
        action="store_true",
        help="Do not inject code_key/spec back into scene_plan.json",
    )
    parser.add_argument("--no-repair", action="store_true", help="Skip repair when output fails validation")
    parser.add_argument("--continue-rounds", type=int, default=2, help="Max continuation rounds for manifest JSON")
    parser.add_argument("--manifest-repair-rounds", type=int, default=2, help="Max repair rounds for scene_codegen.json")
    parser.add_argument("--code-repair-rounds", type=int, default=2, help="Max repair rounds for llm_codegen.py")
    args = parser.parse_args()

    load_dotenv()
    base_llm_cfg = load_zhipu_config()
    generate_llm_cfg = load_zhipu_stage_config("llm_codegen", "generate", base_cfg=base_llm_cfg)
    continue_llm_cfg = load_zhipu_stage_config("llm_codegen", "continue", base_cfg=base_llm_cfg)
    repair_llm_cfg = load_zhipu_stage_config("llm_codegen", "repair", base_cfg=base_llm_cfg)

    case_dir = Path(args.case)
    plan_path = Path(args.plan) if args.plan else (case_dir / "scene_plan.json")
    problem_path = Path(args.problem) if args.problem else (case_dir / "problem.md")
    semantic_path = Path(args.semantic) if args.semantic else (case_dir / "scene_semantic.json")
    scene_codegen_path = case_dir / "scene_codegen.json"
    code_path = case_dir / "llm_codegen.py"

    if args.targets_from == "plan" and not plan_path.exists():
        print(f"Missing scene plan file: {plan_path}", file=sys.stderr)
        return 2
    if args.targets_from == "semantic" and not semantic_path.exists():
        print(f"Missing semantic file for --targets-from semantic: {semantic_path}", file=sys.stderr)
        return 2
    if args.semantic and not semantic_path.exists():
        print(f"Missing specified semantic file: {semantic_path}", file=sys.stderr)
        return 2

    plan_data: dict[str, Any] | None = None
    semantic_data = _load_optional_json(semantic_path)
    if args.targets_from == "plan":
        plan_data = json.loads(plan_path.read_text(encoding="utf-8"))
        plan = ScenePlan.model_validate(plan_data)
        custom_targets, codegen_markers, selection_mode = _collect_custom_targets(plan)
    else:
        if not isinstance(semantic_data, dict):
            print(f"Failed to load semantic data from: {semantic_path}", file=sys.stderr)
            return 2
        custom_targets, codegen_markers, selection_mode = _collect_custom_targets_from_semantic(semantic_data)

    target_ids = set(custom_targets.keys())

    if not target_ids:
        empty = SceneCodegenPlan(version="0.1", objects=[])
        scene_codegen_path.write_text(
            json.dumps(empty.model_dump(mode="json"), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        if not code_path.exists():
            code_path.write_text("BUILDERS = {}\nUPDATERS = {}\n", encoding="utf-8")
        print(str(scene_codegen_path))
        print(str(code_path))
        return 0

    problem = problem_path.read_text(encoding="utf-8") if problem_path.exists() else ""
    if args.targets_from == "plan":
        assert plan_data is not None
        scene_usage = _scene_usage_for_targets(plan_data, target_ids)
    else:
        assert isinstance(semantic_data, dict)
        scene_usage = _scene_usage_for_targets_in_semantic(semantic_data, target_ids)
    semantic_hints = _semantic_hints_by_object(semantic_data, target_ids)

    manifest_prompt = compose_prompt("llm_codegen_manifest")
    manifest_system_prompt_path = case_dir / "llm_codegen_manifest_system_prompt.txt"
    manifest_system_prompt_path.write_text(manifest_prompt.strip() + "\n", encoding="utf-8")
    manifest_payload = _build_manifest_user_payload(
        problem=problem,
        custom_targets=custom_targets,
        codegen_markers=codegen_markers,
        selection_mode=selection_mode,
        scene_usage=scene_usage,
        semantic_hints=semantic_hints,
    )

    manifest_raw = chat_completion(
        [ChatMessage(role="system", content=manifest_prompt), ChatMessage(role="user", content=manifest_payload)],
        cfg=generate_llm_cfg,
    )
    manifest_raw, manifest_cont_chunks = continue_json_output(
        manifest_raw,
        system_prompt=manifest_prompt,
        user_payload=manifest_payload,
        parse_fn=load_json_from_llm,
        max_rounds=args.continue_rounds,
        llm_cfg=continue_llm_cfg,
    )
    (case_dir / "llm_codegen_manifest_raw.txt").write_text(manifest_raw.strip() + "\n", encoding="utf-8")
    _write_continuation_chunks(case_dir, "llm_codegen_manifest_continue_raw", manifest_cont_chunks)

    manifest, manifest_errors = _parse_manifest_and_validate(manifest_raw, target_ids=target_ids)
    manifest_errors_path = case_dir / "llm_codegen_manifest_validation_errors.txt"
    manifest_log: list[str] = []
    if manifest_errors:
        manifest_log.append("[initial]")
        manifest_log.extend(manifest_errors)
        manifest_log.append("")

    if manifest_errors and args.no_repair:
        manifest_errors_path.write_text("\n".join(manifest_log).strip() + "\n", encoding="utf-8")
        print(
            "LLM-codegen manifest invalid. "
            f"See: {case_dir / 'llm_codegen_manifest_raw.txt'} and {manifest_errors_path}",
            file=sys.stderr,
        )
        return 2

    if manifest_errors:
        current_content = manifest_raw
        repair_raw_path = case_dir / "llm_codegen_manifest_repair_raw.txt"
        for round_index in range(1, max(1, args.manifest_repair_rounds) + 1):
            repair_payload = _build_manifest_repair_payload(
                problem=problem,
                custom_targets=custom_targets,
                codegen_markers=codegen_markers,
                selection_mode=selection_mode,
                scene_usage=scene_usage,
                semantic_hints=semantic_hints,
                raw_content=current_content,
                errors=manifest_errors,
                round_index=round_index,
            )
            repaired = chat_completion(
                [ChatMessage(role="system", content=manifest_prompt), ChatMessage(role="user", content=repair_payload)],
                cfg=repair_llm_cfg,
            )
            repaired, repair_cont_chunks = continue_json_output(
                repaired,
                system_prompt=manifest_prompt,
                user_payload=repair_payload,
                parse_fn=load_json_from_llm,
                max_rounds=args.continue_rounds,
                llm_cfg=continue_llm_cfg,
            )
            repair_raw_path.write_text(repaired.strip() + "\n", encoding="utf-8")
            (case_dir / f"llm_codegen_manifest_repair_raw_round_{round_index}.txt").write_text(
                repaired.strip() + "\n",
                encoding="utf-8",
            )
            _write_continuation_chunks(
                case_dir,
                f"llm_codegen_manifest_repair_continue_raw_r{round_index}",
                repair_cont_chunks,
            )

            manifest, manifest_errors = _parse_manifest_and_validate(repaired, target_ids=target_ids)
            if manifest_errors:
                manifest_log.append(f"[repair_round_{round_index}]")
                manifest_log.extend(manifest_errors)
                manifest_log.append("")
                current_content = repaired
                continue
            break

        if manifest_errors:
            manifest_errors_path.write_text("\n".join(manifest_log).strip() + "\n", encoding="utf-8")
            print(
                "LLM-codegen manifest repair rounds finished but output is still invalid. "
                f"See: {case_dir / 'llm_codegen_manifest_raw.txt'}, {repair_raw_path}, {manifest_errors_path}",
                file=sys.stderr,
            )
            return 2

    assert manifest is not None
    if manifest_errors_path.exists():
        manifest_errors_path.unlink()

    scene_codegen_path.write_text(
        json.dumps(manifest.model_dump(mode="json"), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    code_prompt = compose_prompt("llm_codegen_py")
    code_system_prompt_path = case_dir / "llm_codegen_py_system_prompt.txt"
    code_system_prompt_path.write_text(code_prompt.strip() + "\n", encoding="utf-8")
    existing_code = code_path.read_text(encoding="utf-8") if code_path.exists() else ""
    code_payload = _build_code_user_payload(
        problem=problem,
        manifest=manifest,
        semantic_hints=semantic_hints,
        existing_code=existing_code,
    )

    code_raw = chat_completion(
        [ChatMessage(role="system", content=code_prompt), ChatMessage(role="user", content=code_payload)],
        cfg=generate_llm_cfg,
    )
    (case_dir / "llm_codegen_py_raw.txt").write_text(code_raw.strip() + "\n", encoding="utf-8")

    current_code = _extract_python_code(code_raw)
    code_errors = _validate_codegen_runtime(current_code, manifest, case_dir=case_dir)
    code_errors_path = case_dir / "llm_codegen_py_validation_errors.txt"
    code_log: list[str] = []
    if code_errors:
        code_log.append("[initial]")
        code_log.extend(code_errors)
        code_log.append("")

    if code_errors and args.no_repair:
        code_errors_path.write_text("\n".join(code_log).strip() + "\n", encoding="utf-8")
        print(
            "LLM-codegen python output invalid. "
            f"See: {case_dir / 'llm_codegen_py_raw.txt'} and {code_errors_path}",
            file=sys.stderr,
        )
        return 2

    if code_errors:
        repair_raw_path = case_dir / "llm_codegen_py_repair_raw.txt"
        for round_index in range(1, max(1, args.code_repair_rounds) + 1):
            repair_payload = _build_code_repair_payload(
                problem=problem,
                manifest=manifest,
                semantic_hints=semantic_hints,
                raw_code=current_code,
                errors=code_errors,
                round_index=round_index,
            )
            repaired_raw = chat_completion(
                [ChatMessage(role="system", content=code_prompt), ChatMessage(role="user", content=repair_payload)],
                cfg=repair_llm_cfg,
            )
            repair_raw_path.write_text(repaired_raw.strip() + "\n", encoding="utf-8")
            (case_dir / f"llm_codegen_py_repair_raw_round_{round_index}.txt").write_text(
                repaired_raw.strip() + "\n",
                encoding="utf-8",
            )

            current_code = _extract_python_code(repaired_raw)
            code_errors = _validate_codegen_runtime(current_code, manifest, case_dir=case_dir)
            if code_errors:
                code_log.append(f"[repair_round_{round_index}]")
                code_log.extend(code_errors)
                code_log.append("")
                continue
            break

        if code_errors:
            code_errors_path.write_text("\n".join(code_log).strip() + "\n", encoding="utf-8")
            print(
                "LLM-codegen python repair rounds finished but output is still invalid. "
                f"See: {case_dir / 'llm_codegen_py_raw.txt'}, {repair_raw_path}, {code_errors_path}",
                file=sys.stderr,
            )
            return 2

    if code_errors_path.exists():
        code_errors_path.unlink()

    code_path.write_text(current_code.strip() + "\n", encoding="utf-8")

    apply_plan = (not args.skip_apply_plan) and (plan_data is not None)
    if apply_plan:
        updated_plan, apply_errors = _apply_manifest_to_plan(
            plan_data,
            manifest,
            code_file="llm_codegen.py",
            return_errors=True,
        )
        if apply_errors:
            apply_errors_path = case_dir / "llm_codegen_apply_errors.txt"
            apply_errors_path.write_text("\n".join(f"- {err}" for err in apply_errors) + "\n", encoding="utf-8")
            print(
                "LLM-codegen apply-to-plan failed. "
                f"See: {apply_errors_path}",
                file=sys.stderr,
            )
            return 2
        plan_path.write_text(json.dumps(updated_plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(str(scene_codegen_path))
    print(str(code_path))
    if apply_plan:
        print(str(plan_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
