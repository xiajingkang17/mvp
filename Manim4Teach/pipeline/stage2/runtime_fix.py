from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Callable

from ..core.llm_client import LLMClient
from .io_utils import ensure_dir, write_json, write_text
from .llm_scene import DEFAULT_SCENE_CLASS, normalize_scene_code
from .preview_render import run_preview_render
from .static_checks import run_static_checks


def _clip_text(text: str, *, limit: int) -> str:
    value = str(text or "").strip()
    if len(value) <= limit:
        return value
    return value[:limit] + "..."


def _pick_runtime_summary(lines: list[str]) -> str:
    patterns = (
        re.compile(r"\b[A-Za-z_][A-Za-z0-9_]*Error:\s+.+"),
        re.compile(r"\b[A-Za-z_][A-Za-z0-9_]*Exception:\s+.+"),
        re.compile(r"\btraceback\b", re.IGNORECASE),
    )
    for pattern in patterns:
        for line in reversed(lines):
            if pattern.search(line):
                return line.strip()
    return lines[-1].strip() if lines else ""


def _extract_runtime_snippet(preview_report: dict[str, Any] | None, *, max_lines: int = 32) -> tuple[str, str]:
    if not isinstance(preview_report, dict):
        return "", ""
    render = preview_report.get("render")
    if not isinstance(render, dict):
        return "", ""

    stderr_tail = str(render.get("stderr_tail") or "").strip()
    stdout_tail = str(render.get("stdout_tail") or "").strip()
    text = stderr_tail or stdout_tail
    if not text:
        return "", ""

    lines = [line.rstrip() for line in text.splitlines() if line.strip()]
    if not lines:
        return "", ""
    snippet = "\n".join(lines[-max_lines:])
    summary = _pick_runtime_summary(lines)
    return summary, snippet


def summarize_runtime_error(
    *,
    static_report: dict[str, Any] | None,
    preview_report: dict[str, Any] | None,
) -> dict[str, Any]:
    static_report = static_report or {}
    preview_report = preview_report or {}
    compile_error = _clip_text(str(static_report.get("compile_error") or "").strip(), limit=1200)
    runtime_summary, runtime_snippet = _extract_runtime_snippet(preview_report)

    error_type = ""
    error_message = ""
    if compile_error:
        error_type = "compile_error"
        error_message = compile_error
    elif runtime_summary:
        m = re.match(r"([A-Za-z_][A-Za-z0-9_]*):\s*(.*)", runtime_summary)
        if m:
            error_type = m.group(1)
            error_message = m.group(2).strip()
        else:
            error_type = "runtime_error"
            error_message = runtime_summary
    elif preview_report and not preview_report.get("ok"):
        error_type = "preview_failed"
        error_message = "Manim preview render failed without a concise error summary."

    return {
        "compile_ok": bool(static_report.get("compile_ok", False)),
        "preview_ok": bool(preview_report.get("ok", False)),
        "error_type": error_type,
        "error_message": _clip_text(error_message, limit=400),
        "compile_error": compile_error,
        "runtime_summary": _clip_text(runtime_summary, limit=400),
        "runtime_snippet": _clip_text(runtime_snippet, limit=2400),
    }


def build_runtime_fix_user_prompt(
    *,
    requirement: str,
    analysis_packet: dict[str, Any],
    current_code: str,
    runtime_summary: dict[str, Any],
    scene_class: str = DEFAULT_SCENE_CLASS,
) -> str:
    return (
        "请只修复当前 Manim 代码的运行时/编译错误，目标是尽快恢复可渲染状态。\n\n"
        f"[场景类名]\n{scene_class}\n\n"
        f"[用户需求]\n{requirement.strip()}\n\n"
        "[一级分析包 analysis_packet]\n"
        f"{json.dumps(analysis_packet, ensure_ascii=False, indent=2)}\n\n"
        "[错误摘要]\n"
        f"{json.dumps(runtime_summary, ensure_ascii=False, indent=2)}\n\n"
        "[当前代码]\n"
        f"{current_code}\n\n"
        "[要求]\n"
        "1. 只输出完整 Python 代码。\n"
        "2. 类名保持不变。\n"
        "3. 只修复导致编译失败、预览失败的根因，不要重写整题结构。\n"
        "4. 不要做画面美化、节奏重排、教学内容扩写。\n"
        "5. 优先修：未定义变量、错误 API 调用、对象生命周期、资源路径、语法/缩进错误。\n"
    )


def revise_runtime_code(
    *,
    client: LLMClient,
    requirement: str,
    analysis_packet: dict[str, Any],
    current_code: str,
    runtime_summary: dict[str, Any],
    out_dir: Path,
    scene_class: str = DEFAULT_SCENE_CLASS,
) -> tuple[str, Path]:
    system = client.load_stage_system_prompt("runtime_fix")
    user_prompt = build_runtime_fix_user_prompt(
        requirement=requirement,
        analysis_packet=analysis_packet,
        current_code=current_code,
        runtime_summary=runtime_summary,
        scene_class=scene_class,
    )
    raw = client.chat(
        stage_key="runtime_fix",
        mode="generate",
        system_prompt=system,
        user_prompt=user_prompt,
    )
    class_name, code = normalize_scene_code(raw, scene_class=scene_class)
    write_text(out_dir / "llm2_runtime_fix_system_prompt.md", system)
    write_text(out_dir / "llm2_runtime_fix_user_prompt.md", user_prompt)
    write_text(out_dir / "llm2_runtime_fix_raw.txt", raw)
    scene_path = out_dir / "scene.py"
    write_text(scene_path, code)
    return class_name, scene_path


def run_runtime_fix_loop(
    *,
    client: LLMClient,
    requirement: str,
    analysis_packet: dict[str, Any],
    scene_path: Path,
    class_name: str,
    static_report: dict[str, Any],
    preview_report: dict[str, Any] | None,
    out_dir: Path,
    round_index: int,
    max_attempts: int = 2,
    scene_class: str = DEFAULT_SCENE_CLASS,
    static_check_fn: Callable[[Path], dict[str, Any]] = run_static_checks,
    render_fn: Callable[..., dict[str, Any]] = run_preview_render,
    write_report_path: Path | None = None,
) -> dict[str, Any]:
    current_scene_path = scene_path
    current_class_name = class_name
    current_static_report = static_report
    current_preview_report = preview_report
    attempts: list[dict[str, Any]] = []

    if bool(current_static_report.get("compile_ok", False)) and bool((current_preview_report or {}).get("ok", False)):
        report = {
            "status": "not_needed",
            "fixed": True,
            "attempt_count": 0,
            "class_name": current_class_name,
            "scene_path": str(current_scene_path),
            "static_report": current_static_report,
            "preview_report": current_preview_report,
            "attempts": attempts,
        }
        if write_report_path is not None:
            write_json(write_report_path, report)
        return report

    for attempt_index in range(1, max(1, int(max_attempts)) + 1):
        attempt_dir = ensure_dir(out_dir / f"attempt_{attempt_index:02d}")
        runtime_summary = summarize_runtime_error(
            static_report=current_static_report,
            preview_report=current_preview_report,
        )
        fixed_class_name, fixed_scene_path = revise_runtime_code(
            client=client,
            requirement=requirement,
            analysis_packet=analysis_packet,
            current_code=current_scene_path.read_text(encoding="utf-8"),
            runtime_summary=runtime_summary,
            out_dir=attempt_dir,
            scene_class=scene_class or current_class_name,
        )
        new_static_report = static_check_fn(fixed_scene_path)
        new_preview_report = render_fn(
            scene_path=fixed_scene_path,
            class_name=fixed_class_name,
            out_dir=attempt_dir / "preview",
            round_index=round_index,
            write_report_path=attempt_dir / "preview_report.json",
        )

        attempt_record = {
            "attempt_index": attempt_index,
            "runtime_summary": runtime_summary,
            "scene_path": str(fixed_scene_path),
            "class_name": fixed_class_name,
            "static_report": new_static_report,
            "preview_report": new_preview_report,
        }
        attempts.append(attempt_record)

        current_scene_path = fixed_scene_path
        current_class_name = fixed_class_name
        current_static_report = new_static_report
        current_preview_report = new_preview_report
        if bool(new_static_report.get("compile_ok", False)) and bool(new_preview_report.get("ok", False)):
            report = {
                "status": "fixed",
                "fixed": True,
                "attempt_count": attempt_index,
                "class_name": current_class_name,
                "scene_path": str(current_scene_path),
                "static_report": current_static_report,
                "preview_report": current_preview_report,
                "attempts": attempts,
            }
            if write_report_path is not None:
                write_json(write_report_path, report)
            return report

    report = {
        "status": "exhausted",
        "fixed": False,
        "attempt_count": len(attempts),
        "class_name": current_class_name,
        "scene_path": str(current_scene_path),
        "static_report": current_static_report,
        "preview_report": current_preview_report,
        "attempts": attempts,
    }
    if write_report_path is not None:
        write_json(write_report_path, report)
    return report
