from __future__ import annotations

import json
import re


_FULLWIDTH_TRANSLATION = str.maketrans(
    {
        "\uff5b": "{",
        "\uff5d": "}",
        "\uff3b": "[",
        "\uff3d": "]",
    }
)

_FENCE_LINE_RE = re.compile(r"^\s*```[A-Za-z0-9_-]*\s*$")


def normalize_jsonish(text: str) -> str:
    return str(text or "").translate(_FULLWIDTH_TRANSLATION)


def strip_code_fences(text: str) -> str:
    s = normalize_jsonish(text).strip()
    if "```" not in s:
        return s

    lines = s.splitlines()
    for start, line in enumerate(lines):
        if not _FENCE_LINE_RE.match(line):
            continue
        end = None
        for idx in range(start + 1, len(lines)):
            if _FENCE_LINE_RE.match(lines[idx]):
                end = idx
                break
        body = lines[start + 1 : end] if end is not None else lines[start + 1 :]
        return "\n".join(body).strip()
    return s


def extract_first_json(text: str) -> str:
    s = strip_code_fences(text)
    first_obj = s.find("{")
    first_arr = s.find("[")
    if first_obj == -1 and first_arr == -1:
        raise ValueError("未找到 JSON 起始符号")

    if first_obj == -1:
        start = first_arr
        open_ch, close_ch = "[", "]"
    elif first_arr == -1:
        start = first_obj
        open_ch, close_ch = "{", "}"
    else:
        start = min(first_obj, first_arr)
        open_ch, close_ch = ("{", "}") if start == first_obj else ("[", "]")

    depth = 0
    end = None
    for idx in range(start, len(s)):
        ch = s[idx]
        if ch == open_ch:
            depth += 1
        elif ch == close_ch:
            depth -= 1
            if depth == 0:
                end = idx + 1
                break
    if end is None:
        raise ValueError("JSON 不完整，缺少闭合括号")
    return s[start:end].strip()


def load_json_from_llm(text: str):
    normalized = normalize_jsonish(text)
    try:
        return json.loads(normalized)
    except json.JSONDecodeError:
        snippet = extract_first_json(normalized)
        return json.loads(snippet)

