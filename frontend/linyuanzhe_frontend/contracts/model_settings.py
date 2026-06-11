from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, Iterable, List, Mapping

from .runtime_snapshot import digest_text, safe_path_setting_value, safe_text
from .provider_settings import normalize_host_access_scope


MODEL_CUSTOM_SENTINEL = "自定义模型名"
PROVIDER_OPTIONS: List[str] = ["deepseek", "openai", "openai_compatible", "qwen", "zhipu", "local", "custom"]
PROVIDER_DISPLAY_NAMES: Dict[str, str] = {
    "deepseek": "DeepSeek",
    "openai": "OpenAI",
    "openai_compatible": "OpenAI-Compatible / 兼容网关",
    "qwen": "Qwen / 通义千问",
    "zhipu": "Zhipu / 智谱",
    "local": "本地模型",
    "custom": "自定义服务商",
}
PROVIDERS_ALLOWING_CUSTOM_MODEL = {"deepseek", "openai", "openai_compatible", "qwen", "zhipu", "local", "custom"}
DEFAULT_PROVIDER_BASE_URLS: Dict[str, str] = {
    "deepseek": "https://api.deepseek.com",
    "openai": "https://api.openai.com/v1",
    "openai_compatible": "",
    "qwen": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "zhipu": "https://open.bigmodel.cn/api/paas/v4",
    "local": "http://127.0.0.1:8000/v1",
    "custom": "",
}


@dataclass(frozen=True)
class ModelOption:
    """Frontend-only model catalog item.

    This catalog is a local search/filter source for the Settings page. It does
    not call provider SDKs, browse the network, or validate credentials. L6.72.23
    binds model choices to the selected Provider and keeps a custom model input
    for fast-moving OpenAI / OpenAI-compatible / local model names.
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
        provider = normalize_provider_value(data.get("provider", "unknown"))
        return cls(
            provider=provider,
            model_id=safe_text(data.get("model_id", ""), 100),
            display_name=safe_text(data.get("display_name", ""), 120),
            context_window=safe_text(data.get("context_window", "unknown"), 40),
            tags=tags,
            status=safe_text(data.get("status", "available_placeholder"), 40),
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


DEFAULT_MODEL_CATALOG: List[ModelOption] = [
    ModelOption("deepseek", "deepseek-v4-pro", "DeepSeek V4 Pro 官方兼容主模型", "1M", ["reasoning", "deepseek", "primary"]),
    ModelOption("deepseek", "deepseek-v4-flash", "DeepSeek V4 Flash 快速回退模型", "1M", ["fast", "deepseek", "fallback"]),
    ModelOption("deepseek", "deepseek-reasoner", "DeepSeek Reasoner 兼容保留", "128K", ["reasoning", "legacy", "long-chain"]),
    ModelOption("deepseek", "deepseek-chat", "DeepSeek Chat 兼容保留", "128K", ["chat", "legacy", "daily"]),
    ModelOption("openai", "gpt-4.1", "OpenAI 常用模型占位；可手填更新模型名", "long", ["openai", "preset"]),
    ModelOption("openai", "gpt-4o", "OpenAI 多模态兼容占位；可手填更新模型名", "long", ["openai", "preset"]),
    ModelOption("openai", "gpt-4o-mini", "OpenAI 轻量兼容占位；可手填更新模型名", "long", ["openai", "fast"]),
    ModelOption("openai_compatible", "deepseek-v4-pro", "兼容网关示例：DeepSeek V4 Pro", "long", ["gateway", "example"]),
    ModelOption("openai_compatible", "qwen3-max", "兼容网关示例：Qwen3 Max", "long", ["gateway", "example"]),
    ModelOption("qwen", "qwen3-max", "Qwen3 Max 兼容占位", "long", ["fallback", "cn", "tool-use"]),
    ModelOption("qwen", "qwen-plus", "Qwen Plus 兼容占位", "long", ["fallback", "cn"]),
    ModelOption("zhipu", "glm-4.5", "GLM-4.5 兼容占位", "long", ["fallback", "cn"]),
    ModelOption("zhipu", "glm-4-plus", "GLM-4 Plus 兼容占位", "long", ["fallback", "cn"]),
    ModelOption("local", "local-model", "本地 OpenAI-compatible 模型名占位", "local", ["local", "custom"]),
    ModelOption("custom", "custom-model", "自定义服务商模型名占位", "custom", ["custom"]),
]


def normalize_provider_value(value: Any) -> str:
    provider = safe_text(value, 80).strip().lower().replace(" ", "_").replace("-", "_")
    aliases = {
        "openai compatible": "openai_compatible",
        "openai_compat": "openai_compatible",
        "compatible": "openai_compatible",
        "gateway": "openai_compatible",
        "deep_seek": "deepseek",
        "local_model": "local",
        "localhost": "local",
        "自定义": "custom",
    }
    provider = aliases.get(provider, provider)
    return provider if provider in PROVIDER_OPTIONS else "custom"


def provider_display_name(provider: Any) -> str:
    value = normalize_provider_value(provider)
    return PROVIDER_DISPLAY_NAMES.get(value, value)


def provider_allows_custom_model(provider: Any) -> bool:
    return normalize_provider_value(provider) in PROVIDERS_ALLOWING_CUSTOM_MODEL


def default_base_url_for_provider(provider: Any) -> str:
    return DEFAULT_PROVIDER_BASE_URLS.get(normalize_provider_value(provider), "")


def model_options_for_provider(provider: Any, catalog: Iterable[ModelOption] | None = None) -> List[ModelOption]:
    target = normalize_provider_value(provider)
    return [item for item in (catalog or DEFAULT_MODEL_CATALOG) if normalize_provider_value(item.provider) == target]


def default_model_for_provider(provider: Any) -> str:
    target = normalize_provider_value(provider)
    items = model_options_for_provider(target)
    if items:
        return items[0].model_id
    return MODEL_CUSTOM_SENTINEL if provider_allows_custom_model(target) else ""


def model_values_for_provider(provider: Any, query: str = "", *, include_custom: bool = True, catalog: Iterable[ModelOption] | None = None) -> List[str]:
    q = safe_text(query, 120).lower().strip()
    values: List[str] = []
    for item in model_options_for_provider(provider, catalog):
        haystack = " ".join([item.provider, item.model_id, item.display_name, item.context_window, *item.tags]).lower()
        if q and q not in haystack:
            continue
        if item.model_id and item.model_id not in values:
            values.append(item.model_id)
    if include_custom and provider_allows_custom_model(provider) and MODEL_CUSTOM_SENTINEL not in values:
        values.append(MODEL_CUSTOM_SENTINEL)
    return values


def effective_model_name(provider: Any, selected_model: Any, custom_model: Any = "") -> str:
    selected = safe_text(selected_model, 120).strip()
    custom = safe_text(custom_model, 120).strip()
    if selected in {"", MODEL_CUSTOM_SENTINEL, "custom", "custom-model", "自定义"}:
        return custom or default_model_for_provider(provider)
    # OpenAI / compatible / local keep accepting the hand-filled value even if the
    # dropdown currently points at a preset. This prevents stale catalogs from
    # blocking newly released or gateway-specific model identifiers.
    if normalize_provider_value(provider) in {"openai", "openai_compatible", "local", "custom"} and custom:
        return custom
    return selected


def filter_model_catalog(query: str, catalog: Iterable[ModelOption] | None = None, provider: Any | None = None) -> List[ModelOption]:
    """Local model search for the Settings page.

    Search is case-insensitive and frontend-only. When ``provider`` is supplied,
    results are restricted to the selected Provider so the UI cannot present an
    OpenAI model inside DeepSeek, or a DeepSeek preset inside OpenAI unless that
    provider is explicitly OpenAI-compatible / custom.
    """

    items = list(catalog or DEFAULT_MODEL_CATALOG)
    if provider is not None:
        target = normalize_provider_value(provider)
        items = [item for item in items if normalize_provider_value(item.provider) == target]
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
    """Return a L6.72.23-safe settings snapshot.

    API Key remains write-only from the frontend perspective. Base URL is not a
    secret and may be retained for Settings-page display, while logs/reports can
    still use configured flags and stable digests.
    """

    provider = normalize_provider_value(raw.get("provider", "deepseek"))
    selected_model = raw.get("main_model") or raw.get("model") or default_model_for_provider(provider)
    custom_model = raw.get("custom_model") or raw.get("model_custom") or ""
    model = effective_model_name(provider, selected_model, custom_model)
    api_key = str(raw.get("api_key", "") or "")
    base_url = str(raw.get("api_base_url", "") or raw.get("base_url", "") or "")
    key_configured = bool(api_key.strip())
    base_url_configured = bool(base_url.strip())
    host_scope = normalize_host_access_scope(raw.get("host_access_scope", "system_drive"))
    host_root = safe_path_setting_value(raw.get("host_access_root", ""), 520)
    return {
        "provider": provider,
        "provider_label": provider_display_name(provider),
        "main_model": safe_text(model, 120),
        "model": safe_text(model, 120),
        "selected_model": safe_text(selected_model, 120),
        "custom_model_configured": bool(safe_text(custom_model, 120).strip()),
        "api_key_configured": key_configured,
        "api_key_digest": digest_text(api_key, 16) if key_configured else "",
        "base_url_configured": base_url_configured,
        "base_url_digest": digest_text(base_url, 16) if base_url_configured else "",
        "base_url_display": safe_text(base_url, 220) if base_url_configured else "",
        "tool_execution_mode": safe_text(raw.get("tool_execution_mode", "runtime_governed"), 40) or "runtime_governed",
        "host_access_scope": host_scope,
        "host_access_root_configured": bool(host_root.strip()),
        "host_access_root_digest": digest_text(host_root, 16) if host_root.strip() else "",
        "persona_name": safe_text(raw.get("persona_name", "临渊者"), 32) or "临渊者",
        "persona_digest": digest_text(str(raw.get("persona_prompt", "") or ""), 16) if str(raw.get("persona_prompt", "") or "").strip() else "",
        "raw_api_key_persisted": False,
        "raw_base_url_persisted": True,
        "frontend_only": True,
        "no_provider_call": True,
        "no_tool_execution": True,
        "provider_model_binding": True,
    }
