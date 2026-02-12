from __future__ import annotations

from pathlib import Path

from pipeline.config import ROOT_DIR


PROMPTS_DIR = ROOT_DIR / "prompts"


def load_prompt(name: str) -> str:
    """
    读取 prompts/ 下的提示词模板。

    例：load_prompt("llm1_teaching_plan.md")
    """

    path = PROMPTS_DIR / name
    return path.read_text(encoding="utf-8")


def render_template(template: str, *, variables: dict[str, str]) -> str:
    """
    用极简方式渲染模板：把 `{key}` 替换成对应 value。
    """

    result = template
    for key, value in variables.items():
        result = result.replace("{" + key + "}", value)
    return result

