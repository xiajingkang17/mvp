from __future__ import annotations

import json


_FULLWIDTH_TRANSLATION = str.maketrans(
    {
        "｛": "{",
        "｝": "}",
        "［": "[",
        "］": "]",
    }
)


def normalize_jsonish(text: str) -> str:
    """
    Normalize common full-width JSON brackets to ASCII.
    """

    return text.translate(_FULLWIDTH_TRANSLATION)


def strip_code_fences(text: str) -> str:
    s = normalize_jsonish(text).strip()
    if s.startswith("```") and s.endswith("```"):
        lines = s.splitlines()
        if len(lines) >= 3:
            return "\n".join(lines[1:-1]).strip()
    return s


def extract_first_json(text: str) -> str:
    """
    Extract the first JSON object/array from model output.
    """

    s = strip_code_fences(text)

    first_obj = s.find("{")
    first_arr = s.find("[")
    if first_obj == -1 and first_arr == -1:
        raise ValueError("No JSON start token found ('{' or '[').")

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
    for i in range(start, len(s)):
        ch = s[i]
        if ch == open_ch:
            depth += 1
        elif ch == close_ch:
            depth -= 1
            if depth == 0:
                end = i + 1
                break

    if end is None:
        raise ValueError("JSON seems incomplete (missing closing bracket).")

    return s[start:end].strip()


def load_json_from_llm(text: str):
    """
    Parse model output as JSON; fallback to extracting the first JSON snippet.
    """

    normalized = normalize_jsonish(text)
    try:
        return json.loads(normalized)
    except json.JSONDecodeError:
        snippet = extract_first_json(normalized)
        return json.loads(snippet)
