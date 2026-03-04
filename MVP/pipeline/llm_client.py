from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from .env import load_dotenv
from .json_utils import load_json_from_llm
from .llm.anthropic import chat_completion as anthropic_chat_completion
from .llm.anthropic import load_anthropic_stage_config
from .llm.kimi import chat_completion as kimi_chat_completion
from .llm.kimi import load_kimi_stage_config
from .llm.types import ChatMessage, ProviderName
from .llm.zhipu import chat_completion, load_zhipu_stage_config
from .llm_continuation import continue_code_output, continue_json_output


Mode = Literal["generate", "continue", "repair"]


@dataclass(frozen=True)
class LLMStage:
    """把“业务角色”映射到 `configs/llm.yaml` 里的 stage 配置名。"""

    name: str
    provider: ProviderName
    profile_stage: str
    prompt_bundle: str | None = None


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class LLMClient:
    """
    MVP 的最小 LLM 调用封装：
    - 配置优先级与仓库现有实现保持一致（.env -> llm.yaml -> 默认）
    - JSON 输出支持 continuation（防止被截断）
    """

    def __init__(self, *, prompts_dir: Path, stage_map: dict[str, LLMStage]):
        self.prompts_dir = prompts_dir
        self.stage_map = stage_map

    def _cfg(self, stage_key: str, mode: Mode):
        stage = self.stage_map[stage_key]
        if stage.provider == "anthropic":
            return load_anthropic_stage_config(stage=stage.profile_stage, mode=mode)
        if stage.provider == "kimi":
            return load_kimi_stage_config(stage=stage.profile_stage, mode=mode)
        return load_zhipu_stage_config(stage=stage.profile_stage, mode=mode)

    def _chat_completion(self, provider: ProviderName, messages: list[ChatMessage], cfg: Any) -> str:
        if provider == "anthropic":
            return anthropic_chat_completion(messages, cfg=cfg)
        if provider == "kimi":
            return kimi_chat_completion(messages, cfg=cfg)
        return chat_completion(messages, cfg=cfg)

    def chat(self, *, stage_key: str, mode: Mode, system_prompt: str, user_prompt: str) -> str:
        load_dotenv()
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

    def load_system_prompt(self, filename: str) -> str:
        return _read_text(self.prompts_dir / filename)

    def load_prompt_bundle(self, bundle_dir: str) -> str:
        """
        以“文件夹”为单位加载 prompt。

        目录结构约定：
        prompts/<bundle_dir>/
          - bundle.md（可选）：按顺序列出需要拼接的 prompt 文件（相对路径，一行一个）
          - system.md（可选）：若 bundle.md 不存在，则默认读取 system.md

        备注：
        - 允许把每个 LLM 的 prompt 拆成多个文件（算法说明/输出契约/示例等），通过 bundle.md 组合。
        """

        folder = self.prompts_dir / bundle_dir
        if not folder.exists():
            # 兼容旧用法：把参数当成文件名
            return self.load_system_prompt(bundle_dir)

        bundle_path = folder / "bundle.md"
        if not bundle_path.exists():
            bundle_path = folder / "bundle.txt"  # 兼容旧扩展名
        if bundle_path.exists():
            parts: list[str] = []
            for raw_line in bundle_path.read_text(encoding="utf-8").splitlines():
                line = raw_line.strip()
                if not line or line.startswith("#"):
                    continue
                part_path = folder / line
                if not part_path.exists():
                    raise FileNotFoundError(f"prompt bundle 引用的文件不存在: {part_path}")
                parts.append(_read_text(part_path).strip())

            merged = "\n\n".join([p for p in parts if p]).strip()
            if merged:
                return merged + "\n"

        system_path = folder / "system.md"
        if not system_path.exists():
            system_path = folder / "system.txt"  # 兼容旧扩展名
        if system_path.exists():
            return _read_text(system_path)

        raise FileNotFoundError(f"prompt bundle 目录缺少 bundle.md 或 system.md: {folder}")

    def load_stage_system_prompt(self, stage_key: str) -> str:
        """
        根据 stage_key 读取该 stage 对应的 system prompt（通常来自 prompts/<bundle>/...）。
        """

        stage = self.stage_map[stage_key]
        bundle = stage.prompt_bundle or stage.name
        return self.load_prompt_bundle(bundle)

    def generate_json(
        self,
        *,
        stage_key: str,
        system_prompt: str,
        user_prompt: str,
        max_continue_rounds: int = 2,
        repair_rounds: int = 2,
    ) -> tuple[dict[str, Any], str]:
        """
        返回：(json_data, raw_text)
        """

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

        # 尝试直接解析
        try:
            data = load_json_from_llm(merged)
            if isinstance(data, dict):
                return data, merged
        except Exception:  # noqa: BLE001
            pass

        # 解析失败：用 LLM 修 JSON（只要求输出合法 JSON）
        repair_system = "你是严格的 JSON 修复器。你的输出必须是可被 json.loads 解析的 JSON，不能包含任何解释或 Markdown。"
        schema_hint = (
            "请修复并只输出 JSON。"
            "如果原输出缺字段，请补齐为合理默认值；如果字段类型不对，请纠正类型。"
        )

        last_text = merged
        for _ in range(max(0, repair_rounds)):
            repair_user = (
                f"{schema_hint}\n\n"
                "【原始输出】\n"
                f"{last_text}\n"
            )
            repaired = self.chat(stage_key=stage_key, mode="repair", system_prompt=repair_system, user_prompt=repair_user)
            try:
                repaired_merged, _ = continue_json_output(
                    repaired,
                    system_prompt=repair_system,
                    user_payload=repair_user,
                    parse_fn=load_json_from_llm,
                    max_rounds=max_continue_rounds,
                    chat_fn=lambda messages, cfg: self._chat_completion(self.stage_map[stage_key].provider, messages, cfg),
                    llm_cfg=self._cfg(stage_key, "continue"),
                )
                data = load_json_from_llm(repaired_merged)
                if isinstance(data, dict):
                    return data, repaired_merged
            except Exception:  # noqa: BLE001
                last_text = repaired

        raise ValueError("LLM 输出无法解析为 JSON（多轮修复后仍失败）")

    def generate_code(
        self,
        *,
        stage_key: str,
        mode: Mode = "generate",
        system_prompt: str,
        user_prompt: str,
        max_continue_rounds: int = 3,
    ) -> tuple[str, str, list[str]]:
        """
        返回：(merged_code, raw_text, continuation_chunks)
        """

        raw = self.chat(stage_key=stage_key, mode=mode, system_prompt=system_prompt, user_prompt=user_prompt)
        merged, chunks = continue_code_output(
            raw,
            system_prompt=system_prompt,
            user_payload=user_prompt,
            max_rounds=max_continue_rounds,
            chat_fn=lambda messages, cfg: self._chat_completion(self.stage_map[stage_key].provider, messages, cfg),
            llm_cfg=self._cfg(stage_key, "continue"),
        )
        return merged, raw, chunks

    def save_json(self, path: Path, data: dict[str, Any]) -> None:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
