from __future__ import annotations

import json
import os
import socket
import time
import urllib.error
import urllib.request
from dataclasses import dataclass

from pipeline.config import CONFIG_DIR, load_yaml
from pipeline.env import load_dotenv

from .types import ChatMessage, ZhipuMessage


@dataclass(frozen=True)
class ZhipuConfig:
    model: str
    temperature: float
    top_p: float
    max_tokens: int
    timeout_s: int
    retries: int
    retry_backoff_s: float
    base_url: str
    enable_thinking: bool


def _to_bool(value: str | bool | None, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False
    return default


def load_zhipu_config() -> ZhipuConfig:
    """
    Priority:
    1) environment variables (.env)
    2) configs/llm.yaml
    3) built-in defaults
    """

    raw = load_yaml(CONFIG_DIR / "llm.yaml") or {}
    zhipu = raw.get("zhipu", {}) or {}

    model = os.environ.get("ZHIPU_MODEL") or str(zhipu.get("model", "glm-4.7"))
    temperature = float(os.environ.get("ZHIPU_TEMPERATURE") or zhipu.get("temperature", 0.3))
    top_p = float(os.environ.get("ZHIPU_TOP_P") or zhipu.get("top_p", 0.95))
    max_tokens = int(os.environ.get("ZHIPU_MAX_TOKENS") or zhipu.get("max_tokens", 2048))
    timeout_s = int(os.environ.get("ZHIPU_TIMEOUT_S") or zhipu.get("timeout_s", 120))
    retries = int(os.environ.get("ZHIPU_RETRIES") or zhipu.get("retries", 2))
    retry_backoff_s = float(os.environ.get("ZHIPU_RETRY_BACKOFF_S") or zhipu.get("retry_backoff_s", 1.5))
    enable_thinking = _to_bool(
        os.environ.get("ZHIPU_ENABLE_THINKING"),
        _to_bool(zhipu.get("enable_thinking"), False),
    )

    base_url = os.environ.get("ZHIPUAI_BASE_URL") or "https://open.bigmodel.cn/api/paas/v4/"
    return ZhipuConfig(
        model=model,
        temperature=temperature,
        top_p=top_p,
        max_tokens=max_tokens,
        timeout_s=timeout_s,
        retries=max(0, retries),
        retry_backoff_s=max(0.1, retry_backoff_s),
        base_url=base_url,
        enable_thinking=enable_thinking,
    )


def _get_api_key() -> str:
    api_key = os.environ.get("ZHIPUAI_API_KEY") or os.environ.get("ZHIPU_API_KEY")
    if not api_key:
        raise RuntimeError("Missing Zhipu API key. Set ZHIPUAI_API_KEY in .env.")
    return api_key


def _to_zhipu_messages(messages: list[ChatMessage]) -> list[ZhipuMessage]:
    return [{"role": m.role, "content": m.content} for m in messages]


def chat_completion(messages: list[ChatMessage], *, cfg: ZhipuConfig | None = None) -> str:
    """
    Call Zhipu Chat Completions API (OpenAPI v4).
    """

    load_dotenv()
    cfg = cfg or load_zhipu_config()
    api_key = _get_api_key()

    url = cfg.base_url.rstrip("/") + "/chat/completions"
    payload = {
        "model": cfg.model,
        "messages": _to_zhipu_messages(messages),
        "temperature": cfg.temperature,
        "top_p": cfg.top_p,
        "max_tokens": cfg.max_tokens,
        "stream": False,
        # Disable thinking by default so completion tokens are spent on final content.
        "enable_thinking": cfg.enable_thinking,
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
            last_exc = RuntimeError(f"Zhipu API returned HTTP {e.code}: {body}")
            can_retry = e.code >= 500 and attempt < total_attempts - 1
            if not can_retry:
                raise last_exc from e
        except (urllib.error.URLError, TimeoutError, socket.timeout) as e:
            last_exc = RuntimeError(f"Failed to connect to Zhipu API: {e}")
            if attempt >= total_attempts - 1:
                raise last_exc from e

        sleep_s = cfg.retry_backoff_s * (2**attempt)
        time.sleep(sleep_s)

    if raw is None:
        if last_exc is not None:
            raise last_exc
        raise RuntimeError("Zhipu request failed with unknown error")

    data = json.loads(raw)
    choice = (data.get("choices") or [{}])[0]
    message = choice.get("message") or {}
    content = message.get("content") or ""
    if content:
        return content

    reasoning = message.get("reasoning_content")
    finish_reason = choice.get("finish_reason")
    if reasoning:
        raise RuntimeError(
            "Zhipu returned reasoning_content but empty content. "
            "Thinking may have exhausted max_tokens before final answer. "
            f"finish_reason={finish_reason}. Set ZHIPU_ENABLE_THINKING=false or increase ZHIPU_MAX_TOKENS."
        )

    raise RuntimeError(f"Zhipu returned empty content: {data}")
