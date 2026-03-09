from __future__ import annotations

import ast
import json
import re
from pathlib import Path
from typing import Any

from ..core.json_utils import strip_code_fences
from ..core.llm_client import LLMClient
from .io_utils import write_text
from .rubric_loader import build_review_rubric_block


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
        body = (
            "        title = Text('草稿为空，需要修复', font_size=32)\n"
            "        self.play(Write(title))\n"
            "        self.wait(1)"
        )
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
    domain, rubric_block = build_review_rubric_block(
        requirement=requirement,
        analysis_packet=analysis_packet,
    )
    return (
        "请根据以下输入生成第一版可看的 Manim 教学视频代码。\n\n"
        f"[场景类名]\n{scene_class}\n\n"
        f"[用户需求]\n{requirement.strip()}\n\n"
        "[一级分析包 analysis_packet]\n"
        f"{json.dumps(analysis_packet, ensure_ascii=False, indent=2)}\n\n"
        f"[当前学科]\n{domain}\n\n"
        f"{rubric_block}\n"
        "[硬要求]\n"
        "1. 只输出完整 Python 代码。\n"
        "2. 主类名必须是给定类名。\n"
        "3. 至少包含两段有意义的解释性动画。\n"
        "4. 避免全程文字堆叠。\n"
        "5. 尽量遵守解题流程参考：problem_intake -> goal_lock -> model -> method_choice -> derive -> check -> recap -> transfer；可以合并相邻步骤，但不要丢失主线。\n"
        "6. 生成时必须遵守上面的教学图规则：common 始终生效，同时满足当前学科规则；如果涉及空间位置、轨迹、约束或曲线关系，先建立统一定位基准，再放置对象。\n"
    )


def build_visual_fix_user_prompt(
    *,
    requirement: str,
    analysis_packet: dict[str, Any],
    current_code: str,
    vlm_issues: list[dict[str, Any]],
    scene_class: str = DEFAULT_SCENE_CLASS,
) -> str:
    domain, rubric_block = build_review_rubric_block(
        requirement=requirement,
        analysis_packet=analysis_packet,
    )
    return (
        "请根据当前视觉评审问题定向修复 Manim 教学图与动画表达，只处理教学图和视觉结构问题。\n\n"
        f"[场景类名]\n{scene_class}\n\n"
        f"[用户需求]\n{requirement.strip()}\n\n"
        "[一级分析包 analysis_packet]\n"
        f"{json.dumps(analysis_packet, ensure_ascii=False, indent=2)}\n\n"
        f"[当前学科]\n{domain}\n\n"
        f"{rubric_block}\n"
        "[视觉评审问题]\n"
        f"{json.dumps(vlm_issues, ensure_ascii=False, indent=2)}\n\n"
        "[当前代码]\n"
        f"{current_code}\n\n"
        "[要求]\n"
        "1. 只输出完整 Python 代码。\n"
        "2. 类名保持不变。\n"
        "3. 只修复视觉评审指出的教学图问题，不要处理运行时错误，不要重写整题结构。\n"
        "4. 优先修复 high 问题；若命中 spatial_relation_correct 或 constraint_relation_visible，先修图形、轨迹、约束与关键位置关系。\n"
        "5. 若命中 motion_process_readable 或 moving_point_or_tangent_process_readable，优先补过程动画与中间状态，不要只加 FadeIn/FadeOut。\n"
        "6. 保持原有主线与讲解顺序，不要为了美化而大幅重排内容。\n"
        "7. 修稿时遵守上面的教学图规则：common 必须生效，并同时满足当前学科规则。\n"
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


def visual_fix_scene_code(
    *,
    client: LLMClient,
    requirement: str,
    analysis_packet: dict[str, Any],
    current_code: str,
    vlm_issues: list[dict[str, Any]],
    out_dir: Path,
    scene_class: str = DEFAULT_SCENE_CLASS,
) -> tuple[str, Path]:
    system = client.load_stage_system_prompt("visual_fix")
    user_prompt = build_visual_fix_user_prompt(
        requirement=requirement,
        analysis_packet=analysis_packet,
        current_code=current_code,
        vlm_issues=vlm_issues,
        scene_class=scene_class,
    )
    raw = client.chat(
        stage_key="visual_fix",
        mode="generate",
        system_prompt=system,
        user_prompt=user_prompt,
    )
    class_name, code = normalize_scene_code(raw, scene_class=scene_class)
    write_text(out_dir / "llm2_visual_fix_system_prompt.md", system)
    write_text(out_dir / "llm2_visual_fix_user_prompt.md", user_prompt)
    write_text(out_dir / "llm2_visual_fix_raw.txt", raw)
    scene_path = out_dir / "scene.py"
    write_text(scene_path, code)
    return class_name, scene_path
