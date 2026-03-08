from __future__ import annotations

import http.client
import json
import os
import socket
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Literal

from .config import load_llm_yaml
from .env import load_dotenv
from .llm_types import ChatMessage


@dataclass(frozen=True)
class AnthropicConfig:
    model: str
    temperature: float
    top_p: float
    max_tokens: int
    timeout_s: int
    retries: int
    retry_backoff_s: float
    base_url: str
    anthropic_version: str


def _load_anthropic_raw() -> dict[str, Any]:
    raw = load_llm_yaml() or {}
    return raw.get("anthropic", {}) or {}


def load_anthropic_config() -> AnthropicConfig:
    load_dotenv()
    anthropic = _load_anthropic_raw()
    model = os.environ.get("ANTHROPIC_MODEL") or str(anthropic.get("model", "claude-sonnet-4-6"))
    temperature = float(os.environ.get("ANTHROPIC_TEMPERATURE") or anthropic.get("temperature", 0.2))
    top_p = float(os.environ.get("ANTHROPIC_TOP_P") or anthropic.get("top_p", 0.9))
    max_tokens = int(os.environ.get("ANTHROPIC_MAX_TOKENS") or anthropic.get("max_tokens", 3600))
    timeout_s = int(os.environ.get("ANTHROPIC_TIMEOUT_S") or anthropic.get("timeout_s", 240))
    retries = int(os.environ.get("ANTHROPIC_RETRIES") or anthropic.get("retries", 2))
    retry_backoff_s = float(
        os.environ.get("ANTHROPIC_RETRY_BACKOFF_S") or anthropic.get("retry_backoff_s", 1.5)
    )
    base_url = os.environ.get("ANTHROPIC_BASE_URL") or str(
        anthropic.get("base_url", "https://ai.jiexi6.cn/")
    )
    anthropic_version = os.environ.get("ANTHROPIC_VERSION") or str(
        anthropic.get("anthropic_version", "2023-06-01")
    )
    return AnthropicConfig(
        model=model,
        temperature=temperature,
        top_p=top_p,
        max_tokens=max_tokens,
        timeout_s=timeout_s,
        retries=max(0, retries),
        retry_backoff_s=max(0.1, retry_backoff_s),
        base_url=base_url,
        anthropic_version=anthropic_version,
    )


def _build_anthropic_config(base_cfg: AnthropicConfig, overrides: dict[str, Any]) -> AnthropicConfig:
    return AnthropicConfig(
        model=str(overrides.get("model", base_cfg.model)),
        temperature=float(overrides.get("temperature", base_cfg.temperature)),
        top_p=float(overrides.get("top_p", base_cfg.top_p)),
        max_tokens=int(overrides.get("max_tokens", base_cfg.max_tokens)),
        timeout_s=int(overrides.get("timeout_s", base_cfg.timeout_s)),
        retries=max(0, int(overrides.get("retries", base_cfg.retries))),
        retry_backoff_s=max(0.1, float(overrides.get("retry_backoff_s", base_cfg.retry_backoff_s))),
        base_url=str(overrides.get("base_url", base_cfg.base_url)),
        anthropic_version=str(overrides.get("anthropic_version", base_cfg.anthropic_version)),
    )


def load_anthropic_stage_config(
    stage: str,
    mode: Literal["generate", "continue", "repair"],
    *,
    base_cfg: AnthropicConfig | None = None,
) -> AnthropicConfig:
    base = base_cfg or load_anthropic_config()
    anthropic = _load_anthropic_raw()
    stages = anthropic.get("stages", {}) or {}
    if not isinstance(stages, dict):
        return base
    stage_cfg = stages.get(stage, {}) or {}
    if not isinstance(stage_cfg, dict):
        return base
    mode_cfg = stage_cfg.get(mode, {}) or {}
    if not isinstance(mode_cfg, dict):
        return base
    return _build_anthropic_config(base, mode_cfg)


def _get_api_key() -> str:
    api_key = os.environ.get("ANTHROPIC_AUTH_TOKEN") or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Missing Anthropic credential. Set ANTHROPIC_AUTH_TOKEN or ANTHROPIC_API_KEY in Manim4Teach/.env"
        )
    return api_key


def _split_system_messages(messages: list[ChatMessage]) -> tuple[str, list[dict[str, str]]]:
    system_parts: list[str] = []
    payload_messages: list[dict[str, str]] = []
    for message in messages:
        if message.role == "system":
            if message.content.strip():
                system_parts.append(message.content)
            continue
        payload_messages.append({"role": message.role, "content": message.content})
    return "\n\n".join(system_parts).strip(), payload_messages


def _request_text(payload: dict[str, Any], *, cfg: AnthropicConfig, api_key: str) -> str:
    url = cfg.base_url.rstrip("/") + "/v1/messages"
    req = urllib.request.Request(
        url=url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "x-api-key": api_key,
            "anthropic-version": cfg.anthropic_version,
        },
        method="POST",
    )

    raw: str | None = None
    total_attempts = cfg.retries + 1
    last_exc: Exception | None = None
    for attempt in range(total_attempts):
        try:
            with urllib.request.urlopen(req, timeout=cfg.timeout_s) as resp:
                raw = resp.read().decode("utf-8")
            break
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            last_exc = RuntimeError(f"Anthropic API HTTP {exc.code}: {body}")
            can_retry = exc.code >= 500 and attempt < total_attempts - 1
            if not can_retry:
                raise last_exc from exc
        except http.client.IncompleteRead as exc:
            last_exc = RuntimeError("Anthropic response truncated while streaming")
            if attempt >= total_attempts - 1:
                raise last_exc from exc
        except (urllib.error.URLError, TimeoutError, socket.timeout) as exc:
            last_exc = RuntimeError(f"Failed to connect Anthropic API: {exc}")
            if attempt >= total_attempts - 1:
                raise last_exc from exc
        time.sleep(cfg.retry_backoff_s * (2**attempt))

    if raw is None:
        raise last_exc or RuntimeError("Anthropic request failed")

    data = json.loads(raw)
    content = data.get("content") or []
    text_parts = [
        str(block.get("text") or "")
        for block in content
        if isinstance(block, dict) and str(block.get("type") or "") == "text"
    ]
    text = "".join(text_parts).strip()
    if text:
        return text
    raise RuntimeError(f"Anthropic returned empty text content: {data}")


def chat_completion(messages: list[ChatMessage], *, cfg: AnthropicConfig | None = None) -> str:
    load_dotenv()
    cfg = cfg or load_anthropic_config()
    api_key = _get_api_key()

    system_prompt, payload_messages = _split_system_messages(messages)
    payload: dict[str, Any] = {
        "model": cfg.model,
        "messages": payload_messages,
        "temperature": cfg.temperature,
        "top_p": cfg.top_p,
        "max_tokens": cfg.max_tokens,
    }
    if system_prompt:
        payload["system"] = system_prompt

    return _request_text(payload, cfg=cfg, api_key=api_key)


def chat_completion_raw_messages(
    *,
    system_prompt: str,
    messages: list[dict[str, Any]],
    cfg: AnthropicConfig | None = None,
) -> str:
    """
    Send raw Anthropic message blocks, including multimodal blocks.
    """
    load_dotenv()
    cfg = cfg or load_anthropic_config()
    api_key = _get_api_key()

    payload: dict[str, Any] = {
        "model": cfg.model,
        "messages": messages,
        "temperature": cfg.temperature,
        "top_p": cfg.top_p,
        "max_tokens": cfg.max_tokens,
    }
    if str(system_prompt or "").strip():
        payload["system"] = system_prompt

    return _request_text(payload, cfg=cfg, api_key=api_key)
