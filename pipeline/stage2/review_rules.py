from __future__ import annotations

from pathlib import Path
from typing import Any

from .io_utils import write_json


def _issue(severity: str, code: str, message: str) -> dict[str, str]:
    return {"severity": severity, "code": code, "message": message}


def _pick_runtime_summary(lines: list[str]) -> str:
    for line in reversed(lines):
        low = line.lower()
        if "error:" in low or "exception:" in low:
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


def run_rule_review(
    *,
    preview_report: dict[str, Any] | None,
    preview_required: bool = True,
    out_path: Path | None = None,
) -> dict[str, Any]:
    issues: list[dict[str, str]] = []

    if preview_required:
        if preview_report is None:
            issues.append(_issue("high", "preview_missing", "缺少预览结果，无法确认成片可看性。"))
        elif not preview_report.get("ok"):
            summary, snippet = _extract_runtime_snippet(preview_report)
            message = "低清预览渲染失败。请先修复运行错误后再处理画面优化。"
            if summary:
                message += f"\n异常摘要: {summary}"
            if snippet:
                message += f"\nstderr摘录:\n{snippet[:2400]}"
            issues.append(_issue("blocker", "preview_failed", message))
        else:
            duration = float((preview_report.get("artifacts") or {}).get("duration_seconds") or 0.0)
            if duration < 6.0:
                issues.append(_issue("medium", "duration_short", "成片过短，讲解完整性可能不足。"))

    severity_rank = {"blocker": 3, "high": 2, "medium": 1, "low": 0}
    max_severity = "low"
    for item in issues:
        if severity_rank[item["severity"]] > severity_rank[max_severity]:
            max_severity = item["severity"]

    should_revise = any(item["severity"] in {"blocker", "high"} for item in issues)
    report = {
        "max_severity": max_severity,
        "issue_count": len(issues),
        "issues": issues,
        "top_issues": issues[:5],
        "should_revise": should_revise,
    }
    if out_path is not None:
        write_json(out_path, report)
    return report
