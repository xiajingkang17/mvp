from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass

from pipeline.config import CONFIG_DIR, load_yaml

from .types import ChatMessage, ZhipuMessage


@dataclass(frozen=True)
class ZhipuConfig:
    model: str
    temperature: float
    top_p: float
    max_tokens: int
    timeout_s: int
    base_url: str


def load_zhipu_config() -> ZhipuConfig:
    """
    优先级：
    1) 环境变量（.env）
    2) configs/llm.yaml
    3) 内置默认值
    """

    raw = load_yaml(CONFIG_DIR / "llm.yaml") or {}
    zhipu = raw.get("zhipu", {}) or {}

    model = os.environ.get("ZHIPU_MODEL") or str(zhipu.get("model", "glm-4.7"))
    temperature = float(os.environ.get("ZHIPU_TEMPERATURE") or zhipu.get("temperature", 0.3))
    top_p = float(os.environ.get("ZHIPU_TOP_P") or zhipu.get("top_p", 0.95))
    max_tokens = int(os.environ.get("ZHIPU_MAX_TOKENS") or zhipu.get("max_tokens", 2048))
    timeout_s = int(os.environ.get("ZHIPU_TIMEOUT_S") or zhipu.get("timeout_s", 120))

    base_url = os.environ.get("ZHIPUAI_BASE_URL") or "https://open.bigmodel.cn/api/paas/v4/"
    return ZhipuConfig(
        model=model,
        temperature=temperature,
        top_p=top_p,
        max_tokens=max_tokens,
        timeout_s=timeout_s,
        base_url=base_url,
    )


def _get_api_key() -> str:
    api_key = os.environ.get("ZHIPUAI_API_KEY") or os.environ.get("ZHIPU_API_KEY")
    if not api_key:
        raise RuntimeError("未找到智谱 API Key：请在 .env 中设置 ZHIPUAI_API_KEY")
    return api_key


def _to_zhipu_messages(messages: list[ChatMessage]) -> list[ZhipuMessage]:
    return [{"role": m.role, "content": m.content} for m in messages]


def chat_completion(messages: list[ChatMessage], *, cfg: ZhipuConfig | None = None) -> str:
    """
    调用智谱 Chat Completions（OpenAPI v4）。
    文档参考：open.bigmodel.cn
    """

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

    try:
        with urllib.request.urlopen(req, timeout=cfg.timeout_s) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"智谱接口返回 HTTP {e.code}: {body}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"无法连接智谱接口：{e}") from e

    data = json.loads(raw)
    try:
        return data["choices"][0]["message"]["content"]
    except Exception as e:  # noqa: BLE001
        raise RuntimeError(f"无法解析智谱返回：{data}") from e

