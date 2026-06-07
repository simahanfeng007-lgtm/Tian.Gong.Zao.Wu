from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, Iterable, List, Mapping

from .runtime_snapshot import digest_text, safe_text


@dataclass(frozen=True)
class ModelOption:
    """Frontend-only model catalog item.

    This catalog is a local search/filter source for the Settings page. It does
    not call provider SDKs, browse the network, or validate credentials.
    """

    provider: str
    model_id: str
    display_name: str
    context_window: str
    tags: List[str]
    status: str = "available_placeholder"

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "ModelOption":
        tags = [safe_text(x, 32) for x in data.get("tags", []) or []]
        return cls(
            provider=safe_text(data.get("provider", "unknown"), 40),
            model_id=safe_text(data.get("model_id", ""), 80),
            display_name=safe_text(data.get("display_name", ""), 120),
            context_window=safe_text(data.get("context_window", "unknown"), 40),
            tags=tags,
            status=safe_text(data.get("status", "available_placeholder"), 40),
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


DEFAULT_MODEL_CATALOG: List[ModelOption] = [
    ModelOption("deepseek", "deepseek-reasoner", "DeepSeek Reasoner 主推理模型", "64K+", ["reasoning", "primary", "long-chain"]),
    ModelOption("deepseek", "deepseek-chat", "DeepSeek Chat 通用模型", "64K", ["chat", "fast", "daily"]),
    ModelOption("qwen", "qwen3-max", "Qwen3 Max 兼容占位", "long", ["fallback", "cn", "tool-use"]),
    ModelOption("zhipu", "glm-4.5", "GLM-4.5 兼容占位", "long", ["fallback", "cn"]),
    ModelOption("openai", "gpt-5.5-thinking", "GPT-5.5 Thinking 兼容占位", "long", ["reasoning", "fallback"]),
]


def filter_model_catalog(query: str, catalog: Iterable[ModelOption] | None = None) -> List[ModelOption]:
    """Local model search for the Settings page.

    Search is case-insensitive and frontend-only. Empty query returns the whole
    local catalog.
    """

    items = list(catalog or DEFAULT_MODEL_CATALOG)
    q = safe_text(query, 120).lower().strip()
    if not q:
        return items
    result: List[ModelOption] = []
    for item in items:
        haystack = " ".join([item.provider, item.model_id, item.display_name, item.context_window, *item.tags]).lower()
        if q in haystack:
            result.append(item)
    return result


def sanitize_runtime_settings(raw: Mapping[str, Any]) -> Dict[str, Any]:
    """Return a L6.51.1-safe settings snapshot.

    API Key and Base URL are write-only inputs from the frontend perspective.
    The returned structure deliberately never contains the raw key or raw base
    URL; it only exposes configured flags and stable digests for UI feedback.
    """

    api_key = str(raw.get("api_key", "") or "")
    base_url = str(raw.get("api_base_url", "") or raw.get("base_url", "") or "")
    key_configured = bool(api_key.strip())
    base_url_configured = bool(base_url.strip())
    return {
        "provider": safe_text(raw.get("provider", "deepseek"), 40),
        "main_model": safe_text(raw.get("main_model", "deepseek-reasoner"), 80),
        "api_key_configured": key_configured,
        "api_key_digest": digest_text(api_key, 16) if key_configured else "",
        "base_url_configured": base_url_configured,
        "base_url_digest": digest_text(base_url, 16) if base_url_configured else "",
        "raw_api_key_persisted": False,
        "raw_base_url_persisted": False,
        "frontend_only": True,
        "no_provider_call": True,
        "no_tool_execution": True,
    }
