from __future__ import annotations

import json
import os
import socket
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Literal

from ..config import load_llm_yaml
from ..env import load_dotenv

from .types import ChatMessage


@dataclass(frozen=True)
class KimiConfig:
    model: str
    temperature: float
    top_p: float
    max_tokens: int
    timeout_s: int
    retries: int
    retry_backoff_s: float
    base_url: str


def _load_kimi_raw() -> dict[str, Any]:
    raw = load_llm_yaml() or {}
    return raw.get("kimi", {}) or {}


def load_kimi_config() -> KimiConfig:
    load_dotenv()
    kimi = _load_kimi_raw()

    model = os.environ.get("KIMI_MODEL") or os.environ.get("MOONSHOT_MODEL") or str(
        kimi.get("model", "moonshot-v1-128k")
    )
    temperature = float(
        os.environ.get("KIMI_TEMPERATURE") or os.environ.get("MOONSHOT_TEMPERATURE") or kimi.get("temperature", 0.3)
    )
    top_p = float(os.environ.get("KIMI_TOP_P") or os.environ.get("MOONSHOT_TOP_P") or kimi.get("top_p", 0.95))
    max_tokens = int(
        os.environ.get("KIMI_MAX_TOKENS") or os.environ.get("MOONSHOT_MAX_TOKENS") or kimi.get("max_tokens", 4096)
    )
    timeout_s = int(os.environ.get("KIMI_TIMEOUT_S") or os.environ.get("MOONSHOT_TIMEOUT_S") or kimi.get("timeout_s", 240))
    retries = int(os.environ.get("KIMI_RETRIES") or os.environ.get("MOONSHOT_RETRIES") or kimi.get("retries", 2))
    retry_backoff_s = float(
        os.environ.get("KIMI_RETRY_BACKOFF_S")
        or os.environ.get("MOONSHOT_RETRY_BACKOFF_S")
        or kimi.get("retry_backoff_s", 1.5)
    )
    base_url = (
        os.environ.get("KIMI_BASE_URL")
        or os.environ.get("MOONSHOT_BASE_URL")
        or str(kimi.get("base_url", "https://api.moonshot.cn/v1"))
    )

    return KimiConfig(
        model=model,
        temperature=temperature,
        top_p=top_p,
        max_tokens=max_tokens,
        timeout_s=timeout_s,
        retries=max(0, retries),
        retry_backoff_s=max(0.1, retry_backoff_s),
        base_url=base_url,
    )


def _build_kimi_config(base_cfg: KimiConfig, overrides: dict[str, Any]) -> KimiConfig:
    return KimiConfig(
        model=str(overrides.get("model", base_cfg.model)),
        temperature=float(overrides.get("temperature", base_cfg.temperature)),
        top_p=float(overrides.get("top_p", base_cfg.top_p)),
        max_tokens=int(overrides.get("max_tokens", base_cfg.max_tokens)),
        timeout_s=int(overrides.get("timeout_s", base_cfg.timeout_s)),
        retries=max(0, int(overrides.get("retries", base_cfg.retries))),
        retry_backoff_s=max(0.1, float(overrides.get("retry_backoff_s", base_cfg.retry_backoff_s))),
        base_url=str(overrides.get("base_url", base_cfg.base_url)),
    )


def load_kimi_stage_config(
    stage: str,
    mode: Literal["generate", "continue", "repair"],
    *,
    base_cfg: KimiConfig | None = None,
) -> KimiConfig:
    base = base_cfg or load_kimi_config()
    kimi = _load_kimi_raw()

    stages = kimi.get("stages", {}) or {}
    if not isinstance(stages, dict):
        return base

    stage_cfg = stages.get(stage, {}) or {}
    if not isinstance(stage_cfg, dict):
        return base

    mode_cfg = stage_cfg.get(mode, {}) or {}
    if not isinstance(mode_cfg, dict):
        return base

    return _build_kimi_config(base, mode_cfg)


def _get_api_key() -> str:
    api_key = os.environ.get("KIMI_API_KEY") or os.environ.get("MOONSHOT_API_KEY")
    if not api_key:
        raise RuntimeError("缺少 Kimi API key：请在 MVP/.env 中设置 KIMI_API_KEY=... 或 MOONSHOT_API_KEY=...")
    return api_key


def _to_kimi_messages(messages: list[ChatMessage]) -> list[dict[str, str]]:
    return [{"role": m.role, "content": m.content} for m in messages]


def chat_completion(messages: list[ChatMessage], *, cfg: KimiConfig | None = None) -> str:
    load_dotenv()
    cfg = cfg or load_kimi_config()
    api_key = _get_api_key()

    url = cfg.base_url.rstrip("/") + "/chat/completions"
    payload = {
        "model": cfg.model,
        "messages": _to_kimi_messages(messages),
        "temperature": cfg.temperature,
        "top_p": cfg.top_p,
        "max_tokens": cfg.max_tokens,
        "stream": False,
    }

    req = urllib.request.Request(
        url=url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    raw: str | None = None
    last_exc: Exception | None = None
    total_attempts = cfg.retries + 1
    for attempt in range(total_attempts):
        try:
            with urllib.request.urlopen(req, timeout=cfg.timeout_s) as resp:
                raw = resp.read().decode("utf-8")
            break
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            last_exc = RuntimeError(f"Kimi API 返回 HTTP {e.code}: {body}")
            can_retry = e.code >= 500 and attempt < total_attempts - 1
            if not can_retry:
                raise last_exc from e
        except (urllib.error.URLError, TimeoutError, socket.timeout) as e:
            last_exc = RuntimeError(f"连接 Kimi API 失败: {e}")
            if attempt >= total_attempts - 1:
                raise last_exc from e

        time.sleep(cfg.retry_backoff_s * (2**attempt))

    if raw is None:
        if last_exc is not None:
            raise last_exc
        raise RuntimeError("Kimi 请求失败（未知错误）")

    data = json.loads(raw)
    choice = (data.get("choices") or [{}])[0]
    message = choice.get("message") or {}
    content = message.get("content") or ""
    if content:
        return content

    raise RuntimeError(f"Kimi 返回空内容: {data}")
