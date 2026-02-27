from __future__ import annotations

import ast
from dataclasses import dataclass

from .rendering import detect_scene_classes


@dataclass(frozen=True)
class PreflightResult:
    ok: bool
    issues: list[str]


# 这些基本都是 manimlib/旧分支 API 的典型痕迹；在 CE v0.19+ 下应当避免。
_BANNED_SUBSTRINGS = [
    "manimlib",
    "big_ol_pile_of_manim_imports",
    "TextMobject",
    "TexMobject",
    "ShowCreation",
    "ShowCreationThenFadeOut",
    "FadeInFrom",
    "FadeInFromDown",
    "FadeInFromUp",
    "FadeOutAndShiftDown",
    "FadeOutAndShift",
    "ApplyMethod",
    "GraphScene",
    "CONFIG",
]

_TEX_CALL_NAMES = {"Tex", "MathTex"}


def _extract_constant_str(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def check_codegen(
    *,
    code: str,
    expected_class_name: str = "MainScene",
) -> PreflightResult:
    issues: list[str] = []

    if "from manim import *" not in code:
        issues.append("缺少 `from manim import *`。")

    for s in _BANNED_SUBSTRINGS:
        if s in code:
            issues.append(f"包含禁用字符串：`{s}`（疑似旧版/非 CE API）。")

    scene_classes = detect_scene_classes(code)
    if expected_class_name and expected_class_name not in scene_classes:
        if scene_classes:
            issues.append(
                f"未发现期望的 Scene 类名 `{expected_class_name}`；检测到：{scene_classes}"
            )
        else:
            issues.append(f"未检测到任何 Scene 子类；需要 `class {expected_class_name}(Scene):`。")
    if len(scene_classes) > 1:
        issues.append(f"检测到多个 Scene 子类：{scene_classes}（要求只保留一个）。")

    # AST 静态检查：找出 Tex/MathTex 中的非 ASCII 字符（会导致 latex 编译失败）
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        issues.append(f"Python 语法错误：{exc}")
        return PreflightResult(ok=False, issues=issues)

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue

        func_name: str | None = None
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            # 例如 module.MathTex(...)；一般不会出现，但这里不做处理
            continue

        if func_name not in _TEX_CALL_NAMES:
            continue

        tex_literals: list[str] = []
        for arg in node.args:
            s = _extract_constant_str(arg)
            if s is not None:
                tex_literals.append(s)
        for kw in node.keywords:
            if kw.arg in {"tex_string", "tex_strings"}:
                s = _extract_constant_str(kw.value)
                if s is not None:
                    tex_literals.append(s)

        for s in tex_literals:
            bad = [ch for ch in s if ord(ch) > 127]
            if not bad:
                continue
            uniq = "".join(sorted(set(bad)))
            lineno = getattr(node, "lineno", "?")
            # 只展示一小段，避免把整段公式塞进日志
            snippet = s[:120].replace("\n", "\\n")
            issues.append(
                f"{func_name} 第 {lineno} 行包含非 ASCII 字符：{uniq!r}；片段：{snippet!r}。"
            )

    return PreflightResult(ok=len(issues) == 0, issues=issues)

