from __future__ import annotations

import ast
import builtins
import py_compile
import re
from pathlib import Path
from typing import Any

from .io_utils import write_json


def _compile_check(scene_path: Path) -> tuple[bool, str]:
    try:
        py_compile.compile(str(scene_path), doraise=True)
        return True, ""
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)


def _extract_str_constants(tree: ast.AST) -> list[str]:
    out: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            out.append(node.value)
    return out


def _collect_construct_undefined_name_candidates(tree: ast.AST) -> list[str]:
    builtins_set = set(dir(builtins))
    global_defs: set[str] = set()
    for node in getattr(tree, "body", []):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            global_defs.add(node.name)
        if isinstance(node, ast.Import):
            for alias in node.names:
                global_defs.add((alias.asname or alias.name.split(".")[0]).strip())
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if alias.name == "*":
                    continue
                global_defs.add((alias.asname or alias.name).strip())
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    global_defs.add(target.id)

    candidates: set[str] = set()
    for node in getattr(tree, "body", []):
        if not isinstance(node, ast.ClassDef):
            continue
        for fn in node.body:
            if not isinstance(fn, ast.FunctionDef) or fn.name != "construct":
                continue
            local_defs: set[str] = {arg.arg for arg in fn.args.args}
            for inner in ast.walk(fn):
                if isinstance(inner, ast.Assign):
                    for target in inner.targets:
                        if isinstance(target, ast.Name):
                            local_defs.add(target.id)
                elif isinstance(inner, ast.For) and isinstance(inner.target, ast.Name):
                    local_defs.add(inner.target.id)
                elif isinstance(inner, ast.With):
                    for item in inner.items:
                        if isinstance(item.optional_vars, ast.Name):
                            local_defs.add(item.optional_vars.id)
                elif isinstance(inner, ast.FunctionDef):
                    local_defs.add(inner.name)
                elif isinstance(inner, ast.Name) and isinstance(inner.ctx, ast.Load):
                    name = inner.id
                    if name in local_defs or name in global_defs:
                        continue
                    if name in builtins_set:
                        continue
                    if name in {"self", "np"}:
                        continue
                    if name and name[0].isupper():
                        # 大写开头通常是 manim 类名
                        continue
                    candidates.add(name)
    return sorted(candidates)


def _collect_register_obj_rebuild_ids(code: str) -> dict[str, int]:
    ids: dict[str, int] = {}
    pat = re.compile(r"register_obj\([^,\n]+,[^,\n]+,\s*['\"]([^'\"]+)['\"]")
    for obj_id in pat.findall(code):
        ids[obj_id] = ids.get(obj_id, 0) + 1
    return ids


def run_static_checks(scene_path: Path, *, out_path: Path | None = None) -> dict[str, Any]:
    code = scene_path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(code)
        parse_ok = True
        parse_error = ""
    except SyntaxError as exc:
        tree = ast.parse("pass")
        parse_ok = False
        parse_error = str(exc)

    compile_ok, compile_error = _compile_check(scene_path)
    str_constants = _extract_str_constants(tree)
    long_text_blocks = [s for s in str_constants if len(s.strip()) >= 48]
    undefined_candidates = _collect_construct_undefined_name_candidates(tree) if parse_ok else []

    play_calls = len(re.findall(r"\bself\.play\s*\(", code))
    wait_calls = len(re.findall(r"\bself\.wait\s*\(", code))
    animation_hits = len(
        re.findall(
            r"\b(Create|Transform|ReplacementTransform|FadeIn|FadeOut|Write|GrowArrow|MoveAlongPath|Indicate|Circumscribe)\s*\(",
            code,
        )
    )
    text_calls = len(re.findall(r"\b(Text|MarkupText|MathTex)\s*\(", code))
    subtitle_driver_hits = len(re.findall(r"\b(show_subtitle|run_step)\s*\(", code))
    move_to_origin_hits = len(re.findall(r"\.move_to\s*\(\s*ORIGIN\s*\)", code))
    fit_calls = len(re.findall(r"\bfit_in_zone\s*\(", code))
    place_calls = len(re.findall(r"\bplace_in_zone(?:_anchor)?\s*\(", code))

    out_of_bounds_literal_hits = 0
    for match in re.findall(r"np\.array\(\s*\[\s*([\-0-9.]+)\s*,\s*([\-0-9.]+)\s*,", code):
        try:
            x = abs(float(match[0]))
            y = abs(float(match[1]))
        except ValueError:
            continue
        if x > 8.0 or y > 5.0:
            out_of_bounds_literal_hits += 1

    register_counts = _collect_register_obj_rebuild_ids(code)
    rebuilt_ids = sorted([obj_id for obj_id, count in register_counts.items() if count >= 3])

    # 规则阈值（面向当前两级工作流微调）：
    # 1) 仍优先抓“动画稀缺、居中堆叠、越界”这类高收益问题
    # 2) 下调“文本过多、字幕驱动、fit/place、频繁重建”的敏感度，减少误报
    text_overload_long_block_min = 4
    text_overload_text_calls_min = 16
    subtitle_driver_hits_min = 3
    subtitle_driver_animation_max = 1
    center_stack_hits_min = 4
    fit_without_place_fit_min = 2
    fit_without_place_place_gap_min = 2
    rebuild_frequent_ids_min = 2

    report: dict[str, Any] = {
        "scene_path": str(scene_path),
        "compile_ok": compile_ok,
        "compile_error": compile_error,
        "parse_ok": parse_ok,
        "parse_error": parse_error,
        "undefined_name_candidates": undefined_candidates,
        "metrics": {
            "play_calls": play_calls,
            "wait_calls": wait_calls,
            "animation_hits": animation_hits,
            "text_calls": text_calls,
            "long_text_blocks": len(long_text_blocks),
            "subtitle_driver_hits": subtitle_driver_hits,
            "move_to_origin_hits": move_to_origin_hits,
            "fit_calls": fit_calls,
            "place_calls": place_calls,
            "out_of_bounds_literal_hits": out_of_bounds_literal_hits,
            "register_obj_rebuild_ids": rebuilt_ids,
        },
        "heuristic_flags": {
            "possible_text_overload": (
                len(long_text_blocks) >= text_overload_long_block_min
                or text_calls >= text_overload_text_calls_min
            ),
            "possible_animation_sparse": animation_hits < 2 or play_calls < 3,
            "possible_subtitle_driven": (
                subtitle_driver_hits >= subtitle_driver_hits_min
                and animation_hits <= subtitle_driver_animation_max
            ),
            "possible_center_stack": move_to_origin_hits >= center_stack_hits_min,
            "possible_fit_without_place": (
                fit_calls >= fit_without_place_fit_min
                and (fit_calls - place_calls) >= fit_without_place_place_gap_min
            ),
            "possible_rebuild_frequent": len(rebuilt_ids) >= rebuild_frequent_ids_min,
            "possible_out_of_bounds_literals": out_of_bounds_literal_hits >= 1,
        },
    }
    if out_path is not None:
        write_json(out_path, report)
    return report
