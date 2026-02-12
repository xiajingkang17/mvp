from __future__ import annotations

from components.common.inline_math import (
    has_latex_tokens_outside_inline_math,
    has_unbalanced_inline_math_delimiters,
    split_inline_math_segments,
)


def test_split_inline_math_segments_mixed_text():
    text = "结论：$E_k=\\frac{1}{2}mv^2$，故停止。"
    assert split_inline_math_segments(text) == [
        ("text", "结论："),
        ("math", "E_k=\\frac{1}{2}mv^2"),
        ("text", "，故停止。"),
    ]


def test_split_inline_math_segments_escaped_dollar():
    text = "价格是 \\$5，不是 $x$。"
    assert split_inline_math_segments(text) == [
        ("text", "价格是 $5，不是 "),
        ("math", "x"),
        ("text", "。"),
    ]


def test_split_inline_math_segments_unmatched_opening_delimiter_downgrades_to_text():
    text = "速度为 $v=2"
    assert split_inline_math_segments(text) == [("text", "速度为 $v=2")]


def test_has_unbalanced_inline_math_delimiters():
    assert not has_unbalanced_inline_math_delimiters("A $x$ B")
    assert has_unbalanced_inline_math_delimiters("A $x B")


def test_has_latex_tokens_outside_inline_math():
    assert has_latex_tokens_outside_inline_math("结果为 \\frac{1}{2}mv^2")
    assert not has_latex_tokens_outside_inline_math("结果为 $\\frac{1}{2}mv^2$")
