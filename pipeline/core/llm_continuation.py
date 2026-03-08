from __future__ import annotations

from typing import Any, Callable

from .json_utils import strip_code_fences
from .llm_types import ChatMessage


_CONTINUATION_INSTRUCTION = (
    "你上一次 JSON 输出被截断了。请从末尾继续输出剩余内容。"
    "只输出续写片段，不要重复已有前缀；不要解释；不要 Markdown；不要代码块。"
)


def is_incomplete_json_error(error: Exception) -> bool:
    text = str(error)
    markers = (
        "JSON 不完整",
        "缺少闭合括号",
        "missing closing bracket",
        "Unterminated string",
        "Expecting value",
        "Expecting property name enclosed in double quotes",
    )
    return any(marker in text for marker in markers)


def stitch_continuation(prefix: str, continuation: str, *, max_overlap: int = 4000) -> str:
    left = str(prefix or "")
    right = strip_code_fences(continuation).lstrip()
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


def continue_json_output(
    content: str,
    *,
    system_prompt: str,
    user_payload: str,
    parse_fn: Callable[[str], object],
    max_rounds: int = 2,
    chat_fn: Callable[[list[ChatMessage], Any], str],
    llm_cfg: Any = None,
) -> tuple[str, list[str]]:
    merged = content
    chunks: list[str] = []

    for _ in range(max(0, int(max_rounds))):
        try:
            parse_fn(merged)
            break
        except Exception as exc:  # noqa: BLE001
            if not is_incomplete_json_error(exc):
                break

        continuation = chat_fn(
            [
                ChatMessage(role="system", content=system_prompt),
                ChatMessage(role="user", content=user_payload),
                ChatMessage(role="assistant", content=merged),
                ChatMessage(role="user", content=_CONTINUATION_INSTRUCTION),
            ],
            llm_cfg,
        )
        if not continuation.strip():
            break
        chunks.append(continuation)
        merged = stitch_continuation(merged, continuation)

    return merged, chunks

