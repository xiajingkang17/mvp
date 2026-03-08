from __future__ import annotations

import ast
import json
import re
from pathlib import Path
from typing import Any

from ..core.json_utils import strip_code_fences
from ..core.llm_client import LLMClient
from .io_utils import write_text


DEFAULT_SCENE_CLASS = "GeneratedTeachScene"


def _extract_python_code(raw: str) -> str:
    text = str(raw or "").strip()
    block_re = re.compile(r"```(?:python|py)?\s*(.*?)```", re.IGNORECASE | re.DOTALL)
    m = block_re.search(text)
    if m:
        return m.group(1).strip()
    return strip_code_fences(text).strip()


def _has_scene_class(code: str) -> bool:
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return False
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            for base in node.bases:
                base_name = ""
                if isinstance(base, ast.Name):
                    base_name = base.id
                elif isinstance(base, ast.Attribute):
                    base_name = base.attr
                if base_name == "Scene":
                    return True
    return False


def detect_scene_class_name(code: str, fallback: str = DEFAULT_SCENE_CLASS) -> str:
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return fallback
    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        for base in node.bases:
            if isinstance(base, ast.Name) and base.id == "Scene":
                return node.name
            if isinstance(base, ast.Attribute) and base.attr == "Scene":
                return node.name
    return fallback


def _ensure_import(code: str) -> str:
    if re.search(r"^\s*from\s+manim\s+import\s+\*", code, flags=re.MULTILINE):
        return code
    return "from manim import *\n\n" + code.lstrip()


def _wrap_as_scene_if_needed(code: str, *, scene_class: str) -> str:
    if _has_scene_class(code):
        return code
    body = "\n".join(f"        {line}" if line.strip() else "" for line in code.splitlines())
    if not body.strip():
        body = "        title = Text('草稿生成为空，需修稿', font_size=32)\n        self.play(Write(title))\n        self.wait(1)"
    return (
        f"class {scene_class}(Scene):\n"
        "    def construct(self):\n"
        f"{body}\n"
    )


def normalize_scene_code(raw: str, *, scene_class: str = DEFAULT_SCENE_CLASS) -> tuple[str, str]:
    code = _extract_python_code(raw)
    code = _ensure_import(code)
    code = _wrap_as_scene_if_needed(code, scene_class=scene_class)
    class_name = detect_scene_class_name(code, fallback=scene_class)
    return class_name, code.rstrip() + "\n"


def build_director_draft_user_prompt(
    *,
    requirement: str,
    analysis_packet: dict[str, Any],
    scene_class: str = DEFAULT_SCENE_CLASS,
) -> str:
    return (
        "请根据以下输入生成第一版可看视频代码。\n\n"
        f"[场景类名]\n{scene_class}\n\n"
        f"[用户需求]\n{requirement.strip()}\n\n"
        "[一级分析包 analysis_packet]\n"
        f"{json.dumps(analysis_packet, ensure_ascii=False, indent=2)}\n\n"
        "[硬要求]\n"
        "1. 只输出 Python。\n"
        "2. 主类名必须是给定类名。\n"
        "3. 至少两段有意义动画。\n"
        "4. 避免全程文本堆叠。\n"
        "5. 尽量遵守解题流程参考：problem_intake -> goal_lock -> model -> method_choice -> derive -> check -> recap -> transfer；可合并相邻步骤并在其上扩展细节。\n"
    )


def build_director_revise_user_prompt(
    *,
    requirement: str,
    analysis_packet: dict[str, Any],
    current_code: str,
    rule_issues: list[dict[str, Any]],
    vlm_issues: list[dict[str, Any]],
    scene_class: str = DEFAULT_SCENE_CLASS,
) -> str:
    return (
        "请在当前代码基础上定向修稿，只修高收益问题。\n\n"
        f"[场景类名]\n{scene_class}\n\n"
        f"[用户需求]\n{requirement.strip()}\n\n"
        "[一级分析包 analysis_packet]\n"
        f"{json.dumps(analysis_packet, ensure_ascii=False, indent=2)}\n\n"
        "[规则评审问题]\n"
        f"{json.dumps(rule_issues, ensure_ascii=False, indent=2)}\n\n"
        "[观感评审问题]\n"
        f"{json.dumps(vlm_issues, ensure_ascii=False, indent=2)}\n\n"
        "[当前代码]\n"
        f"{current_code}\n\n"
        "[要求]\n"
        "1. 只输出完整 Python 代码。\n"
        "2. 类名保持不变。\n"
        "3. 优先修复 blocker/high 问题。\n"
        "4. 若规则问题包含运行报错（如 preview_failed/compile_error），必须先修到可渲染通过；在运行错误未修复前，不要做布局美化或动画风格重排。\n"
        "5. 修稿尽量保持并对齐解题流程参考（problem_intake -> goal_lock -> model -> method_choice -> derive -> check -> recap -> transfer），允许在不偏离主线的前提下扩展细节。\n"
    )


def generate_first_draft(
    *,
    client: LLMClient,
    requirement: str,
    analysis_packet: dict[str, Any],
    out_dir: Path,
    scene_class: str = DEFAULT_SCENE_CLASS,
) -> tuple[str, Path]:
    system = client.load_stage_system_prompt("director_draft")
    user_prompt = build_director_draft_user_prompt(
        requirement=requirement,
        analysis_packet=analysis_packet,
        scene_class=scene_class,
    )
    raw = client.chat(
        stage_key="director_draft",
        mode="generate",
        system_prompt=system,
        user_prompt=user_prompt,
    )
    class_name, code = normalize_scene_code(raw, scene_class=scene_class)
    write_text(out_dir / "llm2_draft_system_prompt.md", system)
    write_text(out_dir / "llm2_draft_user_prompt.md", user_prompt)
    write_text(out_dir / "llm2_draft_raw.txt", raw)
    scene_path = out_dir / "scene.py"
    write_text(scene_path, code)
    return class_name, scene_path


def revise_scene_code(
    *,
    client: LLMClient,
    requirement: str,
    analysis_packet: dict[str, Any],
    current_code: str,
    rule_issues: list[dict[str, Any]],
    vlm_issues: list[dict[str, Any]],
    out_dir: Path,
    scene_class: str = DEFAULT_SCENE_CLASS,
) -> tuple[str, Path]:
    system = client.load_stage_system_prompt("director_revise")
    user_prompt = build_director_revise_user_prompt(
        requirement=requirement,
        analysis_packet=analysis_packet,
        current_code=current_code,
        rule_issues=rule_issues,
        vlm_issues=vlm_issues,
        scene_class=scene_class,
    )
    raw = client.chat(
        stage_key="director_revise",
        mode="generate",
        system_prompt=system,
        user_prompt=user_prompt,
    )
    class_name, code = normalize_scene_code(raw, scene_class=scene_class)
    write_text(out_dir / "llm2_revise_system_prompt.md", system)
    write_text(out_dir / "llm2_revise_user_prompt.md", user_prompt)
    write_text(out_dir / "llm2_revise_raw.txt", raw)
    scene_path = out_dir / "scene.py"
    write_text(scene_path, code)
    return class_name, scene_path
