from __future__ import annotations

from typing import Callable

from pipeline.json_utils import strip_code_fences
from pipeline.llm.types import ChatMessage
from pipeline.llm.zhipu import chat_completion


_CONTINUATION_INSTRUCTION = (
    "你上一条 JSON 输出被截断了。请从末尾继续输出剩余内容。"
    "只输出续写片段，不要重复已有前缀，不要解释，不要 Markdown，不要代码块。"
)


def is_incomplete_json_error(error: Exception) -> bool:
    text = str(error)
    markers = (
        "JSON seems incomplete",
        "missing closing bracket",
        "JSON 似乎不完整",
        "未找到闭合括号",
        "Unterminated string",
        "Expecting value",
        "Expecting property name enclosed in double quotes",
    )
    return any(marker in text for marker in markers)


def stitch_continuation(prefix: str, continuation: str, *, max_overlap: int = 4000) -> str:
    left = prefix
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
            ]
        )
        if not continuation.strip():
            break
        chunks.append(continuation)
        merged = stitch_continuation(merged, continuation)

    return merged, chunks
