from __future__ import annotations

import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class StaticCheckResult:
    ok: bool
    py_compile_ok: bool
    pyflakes_ok: bool | None
    py_compile_output: str
    pyflakes_output: str

    def to_report(self) -> str:
        lines = [
            "【静态检查报告】",
            f"- py_compile_ok: {self.py_compile_ok}",
            f"- pyflakes_ok: {self.pyflakes_ok}",
            "",
            "【py_compile 输出】",
            self.py_compile_output.strip() or "<empty>",
            "",
            "【pyflakes 输出】",
            self.pyflakes_output.strip() or "<empty>",
            "",
            "请基于以上报错修复代码，优先处理未定义变量、语法错误、导入错误。",
        ]
        return "\n".join(lines).strip() + "\n"


def _run_cmd(cmd: list[str], *, timeout_s: int = 60) -> tuple[int, str]:
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
        text = ((proc.stdout or "") + ("\n" if proc.stdout and proc.stderr else "") + (proc.stderr or "")).strip()
        return int(proc.returncode), text
    except subprocess.TimeoutExpired as exc:
        out = ((exc.stdout or "") + "\n" + (exc.stderr or "")).strip()
        return 124, (out + f"\n[timeout] {' '.join(cmd)}").strip()


_STAR_IMPORT_RE = re.compile(r"^.+:\d+:\d+: '([^']+)' may be undefined, or defined from star imports: manim$")
_LOWERCASE_MANIM_NAMES = {
    "smooth",
    "linear",
    "there_and_back",
    "there_and_back_with_pause",
    "rush_into",
    "rush_from",
    "slow_into",
}

_BANNED_API_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\bShowCreation\s*\("), "ShowCreation -> 请改用 Create"),
]


def _filter_pyflakes_output(raw: str) -> str:
    if not raw.strip():
        return ""

    kept: list[str] = []
    skipped = 0
    for line in raw.splitlines():
        s = line.strip()
        if not s:
            continue

        if "'from manim import *' used; unable to detect undefined names" in s:
            skipped += 1
            continue

        m = _STAR_IMPORT_RE.match(s)
        if m:
            name = m.group(1)
            # star import 下的“可能未定义”噪声很大：
            # - 大写常量 / 首字母大写类名，通常来自 manim 全量导入，跳过
            # - 仅保留更可疑的局部变量名（arc1/path_up/tmp 等）
            if name in _LOWERCASE_MANIM_NAMES:
                skipped += 1
                continue
            if name.isupper():
                skipped += 1
                continue
            if re.match(r"^[A-Z][A-Za-z0-9_]*$", name):
                skipped += 1
                continue
            if re.match(r"^[a-z_][a-z0-9_]*$", name):
                kept.append(s)
                continue
            kept.append(s)
            continue

        kept.append(s)

    if skipped > 0:
        kept.append(f"[filtered] 已忽略 {skipped} 条 manim star-import 低置信告警")

    return "\n".join(kept).strip()


def _scan_banned_api_usage(py_file: Path) -> list[str]:
    try:
        text = py_file.read_text(encoding="utf-8")
    except Exception:  # noqa: BLE001
        return []

    findings: list[str] = []
    for pattern, hint in _BANNED_API_PATTERNS:
        for m in pattern.finditer(text):
            # 1-based line number
            line_no = text.count("\n", 0, m.start()) + 1
            findings.append(f"{py_file}:{line_no}: banned api: {hint}")
    return findings


def run_static_checks(py_file: Path, *, timeout_s: int = 60) -> StaticCheckResult:
    py_compile_cmd = [sys.executable, "-m", "py_compile", str(py_file)]
    c_rc, c_out = _run_cmd(py_compile_cmd, timeout_s=timeout_s)
    py_compile_ok = c_rc == 0

    pyflakes_cmd = [sys.executable, "-m", "pyflakes", str(py_file)]
    f_rc, f_raw = _run_cmd(pyflakes_cmd, timeout_s=timeout_s)
    f_out = _filter_pyflakes_output(f_raw)

    # 未安装 pyflakes 时给出可见提示，但不阻断主流程（由 py_compile + 后续渲染兜底）。
    no_pyflakes = "No module named pyflakes" in f_raw
    if no_pyflakes:
        pyflakes_ok: bool | None = None
    else:
        # pyflakes 在 star-import 下可能返回非 0，但过滤后如果没有有效问题可视为通过。
        pyflakes_ok = (f_rc == 0) or (not f_out.strip())

    banned = _scan_banned_api_usage(py_file)
    if banned:
        banned_text = "【banned_api 输出】\n" + "\n".join(banned)
        f_out = ((f_out + "\n\n" + banned_text).strip() if f_out.strip() else banned_text)
        pyflakes_ok = False

    ok = py_compile_ok and (pyflakes_ok is True or pyflakes_ok is None)
    return StaticCheckResult(
        ok=ok,
        py_compile_ok=py_compile_ok,
        pyflakes_ok=pyflakes_ok,
        py_compile_output=c_out,
        pyflakes_output=f_out,
    )
