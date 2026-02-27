from __future__ import annotations

import ast
from typing import Callable

from .json_utils import strip_code_fences
from .llm.types import ChatMessage
from .llm.zhipu import ZhipuConfig, chat_completion


_CONTINUATION_INSTRUCTION = (
    "你上一次的 JSON 输出被截断了。请从末尾继续输出剩余内容。"
    "只输出续写片段，不要重复已有前缀；不要解释；不要 Markdown；不要代码块。"
)

_CODE_CONTINUATION_INSTRUCTION = (
    "你上一次输出的 Python 代码被截断了。请从末尾继续输出剩余代码。"
    "只输出续写片段，不要重复已有前缀；不要解释；不要 Markdown；不要代码块。"
    "必须严格保持 Python 缩进层级，不要改写已输出前缀。"
)


def is_incomplete_json_error(error: Exception) -> bool:
    text = str(error)
    markers = (
        "JSON 似乎不完整",
        "缺少闭合括号",
        "missing closing bracket",
        "Unterminated string",
        "Expecting value",
        "Expecting property name enclosed in double quotes",
    )
    return any(marker in text for marker in markers)


def stitch_continuation(
    prefix: str,
    continuation: str,
    *,
    max_overlap: int = 4000,
    preserve_indentation: bool = False,
) -> str:
    left = prefix
    right = strip_code_fences(continuation)
    if preserve_indentation:
        # 代码续写时仅去掉前导空行，保留首行缩进空格。
        right = right.lstrip("\r\n")
    else:
        right = right.lstrip()
    if not right:
        return left

    max_k = min(len(left), len(right), max_overlap)
    overlap = 0
    for k in range(max_k, 0, -1):
        if left[-k:] == right[:k]:
            overlap = k
            break

    if overlap:
        return left + right[overlap:]
    return left + right


def is_incomplete_python_error(error: Exception) -> bool:
    if not isinstance(error, SyntaxError):
        return False
    text = f"{error.msg}".lower()
    markers = (
        "unexpected eof",
        "unterminated string literal",
        "eol while scanning string literal",
        "was never closed",
        "expected an indented block",
    )
    return any(marker in text for marker in markers)


def _try_parse_python(code: str) -> Exception | None:
    try:
        ast.parse(code)
        return None
    except Exception as e:  # noqa: BLE001
        return e


def continue_code_output(
    content: str,
    *,
    system_prompt: str,
    user_payload: str,
    max_rounds: int = 3,
    llm_cfg: ZhipuConfig | None = None,
) -> tuple[str, list[str]]:
    merged = strip_code_fences(content).strip()
    chunks: list[str] = []

    rounds = max(0, int(max_rounds))
    for _ in range(rounds):
        parse_error = _try_parse_python(merged)
        if parse_error is None:
            break
        if not is_incomplete_python_error(parse_error):
            break

        continuation = chat_completion(
            [
                ChatMessage(role="system", content=system_prompt),
                ChatMessage(role="user", content=user_payload),
                ChatMessage(role="assistant", content=merged),
                ChatMessage(role="user", content=_CODE_CONTINUATION_INSTRUCTION),
            ],
            cfg=llm_cfg,
        )
        if not continuation.strip():
            break
        chunks.append(continuation)
        merged = stitch_continuation(merged, continuation, preserve_indentation=True)

    return merged, chunks


def continue_json_output(
    content: str,
    *,
    system_prompt: str,
    user_payload: str,
    parse_fn: Callable[[str], object],
    max_rounds: int = 2,
    llm_cfg: ZhipuConfig | None = None,
) -> tuple[str, list[str]]:
    merged = content
    chunks: list[str] = []

    rounds = max(0, int(max_rounds))
    for _ in range(rounds):
        try:
            parse_fn(merged)
            break
        except Exception as e:  # noqa: BLE001
            if not is_incomplete_json_error(e):
                break

        continuation = chat_completion(
            [
                ChatMessage(role="system", content=system_prompt),
                ChatMessage(role="user", content=user_payload),
                ChatMessage(role="assistant", content=merged),
                ChatMessage(role="user", content=_CONTINUATION_INSTRUCTION),
            ],
            cfg=llm_cfg,
        )
        if not continuation.strip():
            break
        chunks.append(continuation)
        merged = stitch_continuation(merged, continuation)

    return merged, chunks
