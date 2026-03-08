from __future__ import annotations

from typing import Literal

from ..core.config import PROMPTS_DIR
from ..core.llm_client import LLMClient, LLMStage


Provider = Literal["anthropic"]


def build_stage2_client(*, provider: Provider = "anthropic") -> LLMClient:
    stage_map = {
        "director_draft": LLMStage(
            name="director_draft",
            provider=provider,
            profile_stage="director_draft",
            prompt_bundle="llm2_director_draft",
        ),
        "director_revise": LLMStage(
            name="director_revise",
            provider=provider,
            profile_stage="director_revise",
            prompt_bundle="llm2_director_revise",
        ),
    }
    return LLMClient(prompts_dir=PROMPTS_DIR, stage_map=stage_map)
