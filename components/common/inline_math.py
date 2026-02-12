from __future__ import annotations

import re


InlineMathSegment = tuple[str, str]

_LATEX_CMD_RE = re.compile(r"\\[a-zA-Z]+")


def has_unbalanced_inline_math_delimiters(text: str) -> bool:
    in_math = False
    i = 0
    while i < len(text):
        ch = text[i]
        if ch == "\\" and i + 1 < len(text) and text[i + 1] == "$":
            i += 2
            continue
        if ch == "$":
            in_math = not in_math
        i += 1
    return in_math


def split_inline_math_segments(text: str) -> list[InlineMathSegment]:
    segments: list[InlineMathSegment] = []
    buf: list[str] = []
    in_math = False
    i = 0

    def _push(kind: str, value: str) -> None:
        if not value:
            return
        if segments and segments[-1][0] == kind:
            segments[-1] = (kind, segments[-1][1] + value)
            return
        segments.append((kind, value))

    while i < len(text):
        ch = text[i]
        if ch == "\\" and i + 1 < len(text) and text[i + 1] == "$":
            buf.append("$")
            i += 2
            continue
        if ch == "$":
            _push("math" if in_math else "text", "".join(buf))
            buf = []
            in_math = not in_math
            i += 1
            continue
        buf.append(ch)
        i += 1

    _push("math" if in_math else "text", "".join(buf))

    # Unmatched `$` opener: degrade trailing math chunk back to text.
    if in_math:
        tail_text = "$"
        if segments and segments[-1][0] == "math":
            tail_text += segments[-1][1]
            segments.pop()
        _push("text", tail_text)

    return segments


def has_latex_tokens_outside_inline_math(text: str) -> bool:
    for kind, value in split_inline_math_segments(text):
        if kind != "text":
            continue
        if _LATEX_CMD_RE.search(value):
            return True
    return False
