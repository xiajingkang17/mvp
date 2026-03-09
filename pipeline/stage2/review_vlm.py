from __future__ import annotations

import base64
import os
from pathlib import Path
from typing import Any

from ..core.json_utils import load_json_from_llm
from ..core.llm_anthropic import chat_completion_raw_messages, load_anthropic_stage_config
from .io_utils import write_json
from .rubric_loader import build_review_rubric_block


_SEVERITY_ORDER = {"blocker": 3, "high": 2, "medium": 1, "low": 0}
_ALLOWED_SEVERITY = set(_SEVERITY_ORDER)


def _clip_text(text: str, *, limit: int) -> str:
    s = str(text or "").strip()
    if len(s) <= limit:
        return s
    return s[:limit] + "..."


def _guess_media_type(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".jpg", ".jpeg"}:
        return "image/jpeg"
    if suffix == ".png":
        return "image/png"
    if suffix == ".webp":
        return "image/webp"
    return "image/jpeg"


def _to_image_block(path: Path) -> dict[str, Any]:
    media_type = _guess_media_type(path)
    data_b64 = base64.b64encode(path.read_bytes()).decode("ascii")
    return {
        "type": "image",
        "source": {
            "type": "base64",
            "media_type": media_type,
            "data": data_b64,
        },
    }


def _normalize_issue(item: Any) -> dict[str, str] | None:
    if not isinstance(item, dict):
        return None
    sev = str(item.get("severity") or "").strip().lower()
    if sev not in _ALLOWED_SEVERITY:
        sev = "medium"
    code = str(item.get("code") or "vlm_issue").strip().lower().replace(" ", "_")[:48] or "vlm_issue"
    msg = _clip_text(str(item.get("message") or "").strip(), limit=240)
    if not msg:
        return None
    return {"severity": sev, "code": code, "message": msg}


def _normalize_issues(raw_issues: Any) -> list[dict[str, str]]:
    if not isinstance(raw_issues, list):
        return []
    out: list[dict[str, str]] = []
    for item in raw_issues:
        normalized = _normalize_issue(item)
        if normalized is not None:
            out.append(normalized)
    # 按严重度排序，最多保留前 8 条，避免修稿提示过载。
    out.sort(key=lambda x: _SEVERITY_ORDER.get(x["severity"], 0), reverse=True)
    return out[:8]


def _max_severity(issues: list[dict[str, str]]) -> str:
    if not issues:
        return "low"
    return max(issues, key=lambda x: _SEVERITY_ORDER.get(x.get("severity", "low"), 0)).get("severity", "low")


def _build_system_prompt(*, rubric_block: str, domain: str) -> str:
    return (
        "你是教学视频视觉评审器（VLM reviewer）。\n"
        "你会看到 Manim 预览关键帧，请只做教学图与观感评审，不做数学或物理结论正确性裁判。\n"
        "请严格按照给定的教学图规则做评审：所有题都必须满足 common 规则，并同时满足当前学科规则。\n"
        "优先关注：图形/轨迹空间关系是否正确、主体是否明确、过程是否可读、约束或关键关系是否清楚、标签是否附着正确。\n"
        f"当前学科：{domain}\n\n"
        f"{rubric_block}\n"
        "输出必须是 JSON 对象，且只输出 JSON。\n"
        "JSON 结构：\n"
        "{\n"
        "  \"issues\": [\n"
        "    {\"severity\": \"high|medium|low\", \"code\": \"...\", \"message\": \"...\"}\n"
        "  ],\n"
        "  \"strengths\": [\"...\"],\n"
        "  \"overall\": \"一句总评\"\n"
        "}\n"
        "要求：\n"
        "1) 至多给 5 条 issues。\n"
        "2) message 必须具体可执行，禁止空泛评价。\n"
        "3) 优先直接使用规则 code 作为 issue code，例如 spatial_relation_correct、motion_process_readable、constraint_relation_visible。\n"
        "4) 如画面整体可接受，可以 issues 为空数组。"
    )


def _analysis_hint(analysis_packet: dict[str, Any] | None) -> str:
    if not isinstance(analysis_packet, dict):
        return ""
    mode = str(analysis_packet.get("mode") or "").strip()
    if mode == "problem":
        solving = analysis_packet.get("problem_solving") or {}
        if not isinstance(solving, dict):
            solving = {}
        statement = str(solving.get("problem_statement") or "").strip()
        final_answer = str(solving.get("final_answer") or "").strip()
        steps = solving.get("full_solution_steps")
        step_count = len(steps) if isinstance(steps, list) else 0
        return (
            f"mode=problem；题干摘要：{_clip_text(statement, limit=140)}；"
            f"步骤数={step_count}；答案摘要：{_clip_text(final_answer, limit=90)}"
        )
    if mode == "concept":
        tree = analysis_packet.get("knowledge_tree") or {}
        nodes = tree.get("nodes") if isinstance(tree, dict) else []
        edges = tree.get("edges") if isinstance(tree, dict) else []
        return f"mode=concept；知识树规模：nodes={len(nodes) if isinstance(nodes, list) else 0}, edges={len(edges) if isinstance(edges, list) else 0}"
    return ""


def _build_user_text(
    *,
    requirement: str,
    analysis_packet: dict[str, Any] | None,
    image_count: int,
    domain: str,
) -> str:
    hint = _analysis_hint(analysis_packet)
    requirement_text = _clip_text(requirement, limit=300)
    return (
        "请根据以下预览关键帧做视觉评审。\n"
        f"学科：{domain}\n"
        f"需求：{requirement_text}\n"
        f"分析包摘要：{hint or '无'}\n"
        f"关键帧数量：{image_count}\n"
        "请优先判断：空间关系是否画对、过程是否可读、主体与约束关系是否清楚。\n"
        "只输出 JSON，不要输出 Markdown。"
    )


def run_vlm_review(
    *,
    preview_report: dict[str, Any] | None,
    requirement: str = "",
    analysis_packet: dict[str, Any] | None = None,
    out_path: Path | None = None,
) -> dict[str, Any]:
    domain, rubric_block = build_review_rubric_block(
        requirement=requirement,
        analysis_packet=analysis_packet,
    )
    enabled = str(os.environ.get("M4T_ENABLE_VLM", "0")).strip() == "1"
    if not enabled:
        report = {
            "enabled": False,
            "domain": domain,
            "status": "skipped",
            "issues": [],
            "issue_count": 0,
            "max_severity": "low",
            "should_revise": False,
            "notes": "未启用 VLM 评审（设置 M4T_ENABLE_VLM=1 后可启用）。",
        }
        if out_path is not None:
            write_json(out_path, report)
        return report

    if preview_report is None or not preview_report.get("ok"):
        report = {
            "enabled": True,
            "domain": domain,
            "status": "no_preview",
            "issues": [],
            "issue_count": 0,
            "max_severity": "low",
            "should_revise": False,
            "notes": "预览不可用，VLM 评审跳过。",
        }
        if out_path is not None:
            write_json(out_path, report)
        return report

    artifacts = preview_report.get("artifacts") if isinstance(preview_report, dict) else {}
    keyframes_raw = (artifacts or {}).get("keyframes") if isinstance(artifacts, dict) else []
    keyframes = [Path(p) for p in keyframes_raw or [] if str(p).strip()]
    keyframes = [p for p in keyframes if p.exists()]

    if not keyframes:
        report = {
            "enabled": True,
            "domain": domain,
            "status": "no_keyframes",
            "issues": [],
            "issue_count": 0,
            "max_severity": "low",
            "should_revise": False,
            "notes": "未找到可用关键帧，VLM 评审跳过。",
        }
        if out_path is not None:
            write_json(out_path, report)
        return report

    try:
        max_images = int(str(os.environ.get("M4T_VLM_MAX_IMAGES", "3")).strip())
    except ValueError:
        max_images = 3
    max_images = max(1, min(max_images, 6))
    selected = keyframes[:max_images]

    user_blocks: list[dict[str, Any]] = [
        {
            "type": "text",
            "text": _build_user_text(
                requirement=requirement,
                analysis_packet=analysis_packet,
                image_count=len(selected),
                domain=domain,
            ),
        }
    ]
    for image_path in selected:
        user_blocks.append(_to_image_block(image_path))

    try:
        cfg = load_anthropic_stage_config(stage="vlm_review", mode="generate")
        raw = chat_completion_raw_messages(
            system_prompt=_build_system_prompt(rubric_block=rubric_block, domain=domain),
            messages=[{"role": "user", "content": user_blocks}],
            cfg=cfg,
        )
        parsed = load_json_from_llm(raw)
        if not isinstance(parsed, dict):
            raise ValueError("VLM 输出不是 JSON 对象")

        issues = _normalize_issues(parsed.get("issues"))
        max_sev = _max_severity(issues)
        should_revise = any(i.get("severity") in {"blocker", "high"} for i in issues)
        report = {
            "enabled": True,
            "domain": domain,
            "status": "ok",
            "model": cfg.model,
            "used_keyframes": [str(p) for p in selected],
            "issues": issues,
            "top_issues": issues[:5],
            "issue_count": len(issues),
            "max_severity": max_sev,
            "should_revise": should_revise,
            "strengths": parsed.get("strengths") if isinstance(parsed.get("strengths"), list) else [],
            "overall": str(parsed.get("overall") or "").strip(),
            "raw_text_tail": _clip_text(raw, limit=5000),
        }
    except Exception as exc:  # noqa: BLE001
        report = {
            "enabled": True,
            "domain": domain,
            "status": "error",
            "issues": [],
            "top_issues": [],
            "issue_count": 0,
            "max_severity": "low",
            "should_revise": False,
            "notes": f"VLM 评审失败：{exc}",
        }

    if out_path is not None:
        write_json(out_path, report)
    return report
