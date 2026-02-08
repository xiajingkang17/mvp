from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, TypedDict


Role = Literal["system", "user", "assistant"]


@dataclass(frozen=True)
class ChatMessage:
    role: Role
    content: str


class ZhipuMessage(TypedDict):
    role: Role
    content: str

