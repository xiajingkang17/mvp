from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pipeline.config import ROOT_DIR


PROMPTS_DIR = ROOT_DIR / "prompts"


def load_prompt(name: str) -> str:
    """Load a template file from prompts/."""

    path = PROMPTS_DIR / name
    return path.read_text(encoding="utf-8-sig")


def render_template(template: str, *, variables: dict[str, str]) -> str:
    """Simple template rendering with {key} replacements."""

    result = template
    for key, value in variables.items():
        result = result.replace("{" + key + "}", value)
    return result


def _resolve_prompt_path(rel_path: str) -> Path:
    path = (PROMPTS_DIR / rel_path).resolve()
    try:
        path.relative_to(PROMPTS_DIR.resolve())
    except ValueError as exc:
        raise ValueError(f"Prompt path escapes prompts/ directory: {rel_path}") from exc
    return path


def _read_prompt_rel(rel_path: str) -> str:
    path = _resolve_prompt_path(rel_path)
    if not path.exists():
        raise FileNotFoundError(f"Prompt fragment not found: {path}")
    return path.read_text(encoding="utf-8-sig")


def compose_prompt(stage: str, *, context: dict[str, Any] | None = None) -> str:
    """Compose stage system prompt from prompts/bundles/<stage>.json."""

    ctx = context or {}
    bundle_path = PROMPTS_DIR / "bundles" / f"{stage}.json"
    if not bundle_path.exists():
        raise FileNotFoundError(f"Prompt bundle not found for stage '{stage}': {bundle_path}")

    raw = json.loads(bundle_path.read_text(encoding="utf-8-sig"))
    if not isinstance(raw, dict):
        raise ValueError(f"Prompt bundle must be a JSON object: {bundle_path}")

    pieces: list[str] = []
    base = str(raw.get("base", "")).strip()
    if base:
        pieces.append(_read_prompt_rel(base))

    always = raw.get("always")
    if isinstance(always, list):
        for item in always:
            rel = str(item).strip()
            if rel:
                pieces.append(_read_prompt_rel(rel))

    conditional = raw.get("conditional")
    if isinstance(conditional, list):
        for rule in conditional:
            if not isinstance(rule, dict):
                continue
            flag = str(rule.get("when", "")).strip()
            if not flag or not bool(ctx.get(flag)):
                continue
            frags = rule.get("fragments")
            if not isinstance(frags, list):
                continue
            for item in frags:
                rel = str(item).strip()
                if rel:
                    pieces.append(_read_prompt_rel(rel))

    return "\n\n".join(x.strip() for x in pieces if str(x).strip()).strip()
