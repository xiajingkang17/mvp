from __future__ import annotations

import json


_FULLWIDTH_TRANSLATION = str.maketrans(
    {
        "\uff5b": "{",  # ｛
        "\uff5d": "}",  # ｝
        "\uff3b": "[",  # ［
        "\uff3d": "]",  # ］
    }
)


def normalize_jsonish(text: str) -> str:
    """
    规范化模型输出中常见的“全角括号”，提升 JSON 解析稳定性。
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
    从模型输出中提取第一个 JSON object/array 片段。
    """

    s = strip_code_fences(text)

    first_obj = s.find("{")
    first_arr = s.find("[")
    if first_obj == -1 and first_arr == -1:
        raise ValueError("未找到 JSON 起始符号（'{' 或 '['）。")

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
        raise ValueError("JSON 似乎不完整（缺少闭合括号）。")

    return s[start:end].strip()


def load_json_from_llm(text: str):
    """
    尝试把模型输出解析成 JSON；失败则提取第一个 JSON 片段再解析。
    """

    normalized = normalize_jsonish(text)
    try:
        return json.loads(normalized)
    except json.JSONDecodeError:
        snippet = extract_first_json(normalized)
        return json.loads(snippet)

