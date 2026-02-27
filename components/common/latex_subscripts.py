from __future__ import annotations

import re

from components.common.inline_math import split_inline_math_segments


_SIMPLE_ALPHA_RE = re.compile(r"^[A-Za-z]+$")
_WRAPPED_ALPHA_RE = re.compile(r"^\\(text|mathrm)\{([A-Za-z]+)\}$")


def _shorten_subscript_inner(inner: str, *, max_letters: int) -> str:
    direct = _SIMPLE_ALPHA_RE.fullmatch(inner)
    if direct is not None and len(inner) > max_letters:
        return inner[:max_letters]

    wrapped = _WRAPPED_ALPHA_RE.fullmatch(inner)
    if wrapped is not None:
        style = wrapped.group(1)
        letters = wrapped.group(2)
        if len(letters) > max_letters:
            return f"\\{style}{{{letters[:max_letters]}}}"

    return inner


def shorten_latex_subscripts(latex: str, *, max_letters: int = 2) -> str:
    if max_letters <= 0 or "_" not in latex:
        return latex

    out: list[str] = []
    i = 0
    n = len(latex)
    while i < n:
        ch = latex[i]
        if ch != "_" or (i > 0 and latex[i - 1] == "\\") or i + 1 >= n:
            out.append(ch)
            i += 1
            continue

        out.append("_")
        i += 1

        if latex[i] == "{":
            depth = 1
            j = i + 1
            while j < n and depth > 0:
                if latex[j] == "{":
                    depth += 1
                elif latex[j] == "}":
                    depth -= 1
                j += 1

            if depth != 0:
                out.append(latex[i])
                i += 1
                continue

            end = j - 1
            inner = latex[i + 1 : end]
            fixed_inner = _shorten_subscript_inner(inner, max_letters=max_letters)
            out.append("{")
            out.append(fixed_inner)
            out.append("}")
            i = j
            continue

        j = i
        while j < n and latex[j].isalpha():
            j += 1
        if j > i:
            token = latex[i:j]
            if len(token) > max_letters:
                out.append("{")
                out.append(token[:max_letters])
                out.append("}")
            else:
                out.append(token)
            i = j
            continue

        out.append(latex[i])
        i += 1

    return "".join(out)


def has_long_alpha_subscripts(latex: str, *, max_letters: int = 2) -> bool:
    return shorten_latex_subscripts(latex, max_letters=max_letters) != latex


def shorten_inline_math_subscripts(text: str, *, max_letters: int = 2) -> str:
    if "$" not in text:
        return text

    rebuilt: list[str] = []
    changed = False
    for kind, value in split_inline_math_segments(text):
        if kind == "math":
            fixed = shorten_latex_subscripts(value, max_letters=max_letters)
            rebuilt.append(f"${fixed}$")
            if fixed != value:
                changed = True
        else:
            rebuilt.append(value)

    return "".join(rebuilt) if changed else text

