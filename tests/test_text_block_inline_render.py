from __future__ import annotations

import pytest

pytest.importorskip("manim")
from manim import Text, VGroup

from components.base import ComponentDefaults
from components.common.text_block import TextBlock
from schema.scene_plan_models import ObjectSpec


def _defaults() -> ComponentDefaults:
    return ComponentDefaults(
        font="Arial",
        text_font_size=36,
        bullet_font_size=34,
        formula_font_size=48,
    )


def test_text_block_builds_mixed_inline_text_and_math():
    spec = ObjectSpec(
        type="TextBlock",
        params={"text": "结论：$E_k=\\\\frac{1}{2}mv^2$，故停止。"},
        style={},
        priority=1,
    )
    mobj = TextBlock().build(spec, defaults=_defaults())
    assert isinstance(mobj, VGroup)
    assert len(mobj.submobjects) >= 2


def test_text_block_falls_back_to_plain_text_when_math_invalid():
    spec = ObjectSpec(
        type="TextBlock",
        params={"text": "错误片段：$\\\\badcommand{1}$。"},
        style={},
        priority=1,
    )
    mobj = TextBlock().build(spec, defaults=_defaults())
    assert isinstance(mobj, VGroup)
    assert any(isinstance(part, Text) for part in mobj.submobjects)
