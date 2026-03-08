from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from .json_utils import load_json_from_llm
from .llm_anthropic import chat_completion as anthropic_chat_completion
from .llm_anthropic import chat_completion_raw_messages as anthropic_chat_completion_raw_messages
from .llm_anthropic import load_anthropic_stage_config
from .llm_continuation import continue_json_output
from .llm_types import ChatMessage, ProviderName


Mode = Literal["generate", "continue", "repair"]


@dataclass(frozen=True)
class LLMStage:
    name: str
    provider: ProviderName
    profile_stage: str
    prompt_bundle: str | None = None


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class LLMClient:
    def __init__(self, *, prompts_dir: Path, stage_map: dict[str, LLMStage]):
        self.prompts_dir = prompts_dir
        self.stage_map = stage_map

    def _cfg(self, stage_key: str, mode: Mode):
        stage = self.stage_map[stage_key]
        if stage.provider != "anthropic":
            raise NotImplementedError(f"Manim4Teach 当前仅支持 anthropic，收到: {stage.provider}")
        return load_anthropic_stage_config(stage=stage.profile_stage, mode=mode)

    def _chat_completion(self, provider: ProviderName, messages: list[ChatMessage], cfg: Any) -> str:
        if provider != "anthropic":
            raise NotImplementedError(f"Manim4Teach 当前仅支持 anthropic，收到: {provider}")
        return anthropic_chat_completion(messages, cfg=cfg)

    def _chat_completion_raw(
        self,
        provider: ProviderName,
        *,
        system_prompt: str,
        user_blocks: list[dict[str, Any]],
        cfg: Any,
    ) -> str:
        if provider != "anthropic":
            raise NotImplementedError(f"Manim4Teach 当前仅支持 anthropic，收到: {provider}")
        return anthropic_chat_completion_raw_messages(
            system_prompt=system_prompt,
            messages=[{"role": "user", "content": user_blocks}],
            cfg=cfg,
        )

    def chat(self, *, stage_key: str, mode: Mode, system_prompt: str, user_prompt: str) -> str:
        stage = self.stage_map[stage_key]
        cfg = self._cfg(stage_key, mode)
        return self._chat_completion(
            stage.provider,
            [
                ChatMessage(role="system", content=system_prompt),
                ChatMessage(role="user", content=user_prompt),
            ],
            cfg,
        )

    def chat_raw(
        self,
        *,
        stage_key: str,
        mode: Mode,
        system_prompt: str,
        user_blocks: list[dict[str, Any]],
    ) -> str:
        stage = self.stage_map[stage_key]
        cfg = self._cfg(stage_key, mode)
        return self._chat_completion_raw(
            stage.provider,
            system_prompt=system_prompt,
            user_blocks=user_blocks,
            cfg=cfg,
        )

    def load_system_prompt(self, filename: str) -> str:
        return _read_text(self.prompts_dir / filename)

    def load_prompt_bundle(self, bundle_dir: str) -> str:
        folder = self.prompts_dir / bundle_dir
        if not folder.exists():
            return self.load_system_prompt(bundle_dir)

        bundle_path = folder / "bundle.md"
        if not bundle_path.exists():
            bundle_path = folder / "bundle.txt"
        if bundle_path.exists():
            parts: list[str] = []
            for raw_line in bundle_path.read_text(encoding="utf-8").splitlines():
                line = raw_line.strip()
                if not line or line.startswith("#"):
                    continue
                part_path = folder / line
                if not part_path.exists():
                    raise FileNotFoundError(f"prompt bundle reference not found: {part_path}")
                parts.append(_read_text(part_path).strip())
            merged = "\n\n".join([part for part in parts if part]).strip()
            if merged:
                return merged + "\n"

        system_path = folder / "system.md"
        if not system_path.exists():
            system_path = folder / "system.txt"
        if system_path.exists():
            return _read_text(system_path)
        raise FileNotFoundError(f"prompt bundle missing bundle.md or system.md: {folder}")

    def load_stage_system_prompt(self, stage_key: str) -> str:
        stage = self.stage_map[stage_key]
        bundle = stage.prompt_bundle or stage.name
        return self.load_prompt_bundle(bundle)

    def generate_json(
        self,
        *,
        stage_key: str,
        system_prompt: str,
        user_prompt: str,
        user_blocks: list[dict[str, Any]] | None = None,
        max_continue_rounds: int = 2,
        repair_rounds: int = 2,
    ) -> tuple[dict[str, Any], str]:
        if user_blocks:
            raw = self.chat_raw(
                stage_key=stage_key,
                mode="generate",
                system_prompt=system_prompt,
                user_blocks=user_blocks,
            )
            merged = raw
        else:
            raw = self.chat(stage_key=stage_key, mode="generate", system_prompt=system_prompt, user_prompt=user_prompt)
            merged, _chunks = continue_json_output(
                raw,
                system_prompt=system_prompt,
                user_payload=user_prompt,
                parse_fn=load_json_from_llm,
                max_rounds=max_continue_rounds,
                chat_fn=lambda messages, cfg: self._chat_completion(self.stage_map[stage_key].provider, messages, cfg),
                llm_cfg=self._cfg(stage_key, "continue"),
            )

        last_text = merged
        try:
            data = load_json_from_llm(merged)
            if isinstance(data, dict):
                return data, merged
        except Exception:  # noqa: BLE001
            pass

        repair_system = (
            "你是严格的 JSON 修复器。你的输出必须是可被 json.loads 解析的 JSON，"
            "不能包含任何解释或 Markdown。"
        )
        schema_hint = "请修复并且只输出 JSON，缺字段时补合理默认值，类型错误时纠正。"
        for _ in range(max(0, int(repair_rounds))):
            repair_user = f"{schema_hint}\n\n[原始输出]\n{last_text}\n"
            repaired = self.chat(
                stage_key=stage_key,
                mode="repair",
                system_prompt=repair_system,
                user_prompt=repair_user,
            )
            repaired_merged, _ = continue_json_output(
                repaired,
                system_prompt=repair_system,
                user_payload=repair_user,
                parse_fn=load_json_from_llm,
                max_rounds=max_continue_rounds,
                chat_fn=lambda messages, cfg: self._chat_completion(self.stage_map[stage_key].provider, messages, cfg),
                llm_cfg=self._cfg(stage_key, "continue"),
            )
            last_text = repaired_merged
            try:
                data = load_json_from_llm(repaired_merged)
                if isinstance(data, dict):
                    return data, repaired_merged
            except Exception:  # noqa: BLE001
                continue

        preview = (last_text or "").strip()
        if len(preview) > 800:
            preview = preview[:800] + "\n...[truncated]..."
        raise ValueError(
            "LLM 输出无法解析为 JSON（多轮修复后仍失败）\n"
            f"[stage_key] {stage_key}\n"
            "[last_output_preview]\n"
            f"{preview}"
        )

    def save_json(self, path: Path, data: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
