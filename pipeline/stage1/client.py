from __future__ import annotations

from pathlib import Path
from typing import Literal

from ..core.config import PROMPTS_DIR
from ..core.llm_client import LLMClient, LLMStage


Provider = Literal["anthropic"]


def build_stage1_client(
    *,
    provider: Provider = "anthropic",
    prompts_dir: Path | None = None,
) -> LLMClient:
    prompt_root = prompts_dir or PROMPTS_DIR
    stage_map = {
        "analysis_packet": LLMStage(
            name="analysis_packet",
            provider=provider,
            profile_stage="analyst",
            prompt_bundle="llm1_analysis_packet",
        )
    }
    return LLMClient(prompts_dir=prompt_root, stage_map=stage_map)
