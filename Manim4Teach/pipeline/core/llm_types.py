from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


Role = Literal["system", "user", "assistant"]
ProviderName = Literal["anthropic"]


@dataclass(frozen=True)
class ChatMessage:
    role: Role
    content: str
