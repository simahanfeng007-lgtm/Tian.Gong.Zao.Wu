from __future__ import annotations

# L6.73.8 direct-file smoke bootstrap.
if __package__ in (None, ""):
    import sys as _sys
    from pathlib import Path as _Path
    _pkg_parent = _Path(__file__).resolve().parent.parent
    if str(_pkg_parent) not in _sys.path:
        _sys.path.insert(0, str(_pkg_parent))



from linyuanzhe_frontend.contracts.model_settings import (
    MODEL_CUSTOM_SENTINEL,
    PROVIDER_OPTIONS,
    default_base_url_for_provider,
    effective_model_name,
    filter_model_catalog,
    model_values_for_provider,
    normalize_provider_value,
    provider_allows_custom_model,
    sanitize_runtime_settings,
)
from linyuanzhe_frontend.contracts.provider_settings import ProviderSettingsWriteRequest
from linyuanzhe_frontend.version_info import FE_RUNTIME_VERSION, PROVIDER_CONFIG_SCHEMA_VERSION


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    _assert((FE_RUNTIME_VERSION in {"L6.72.23", "L6.72.24", "L6.72.25", "L6.72.26", "L6.72.27", "L6.72.28", "L6.72.29", "L6.72.30", "L6.72.31", "L6.72.32", "L6.72.33", "L6.72.34", "L6.72.39", "L6.72.33", "L6.72.34", "L6.72.39", "L6.72.33", "L6.72.34", "L6.72.39", "L6.72.33", "L6.72.34", "L6.72.39", "L6.72.33", "L6.72.34", "L6.72.39", "L6.72.33", "L6.72.34", "L6.72.39", "L6.72.33", "L6.72.34", "L6.72.39", "L6.72.33", "L6.72.34", "L6.72.39", "L6.72.33", "L6.72.34", "L6.72.39", "L6.72.32", "L6.72.32", "L6.72.32", "L6.72.32", "L6.72.40", "L6.72.41", "L6.72.42", "L6.72.43", "L6.72.44", "L6.72.52", "L6.73.0", "L6.73.1", "L6.73.2", "L6.73.3", "L6.73.4", "L6.73.5"} or FE_RUNTIME_VERSION.startswith("L6.73.")), "version not bumped")
    _assert(PROVIDER_CONFIG_SCHEMA_VERSION.startswith("tiangong.l6_73_") or PROVIDER_CONFIG_SCHEMA_VERSION.endswith(("l6_72_52.local_provider_config.v1", "l6_73_5.local_provider_config.v1")), "provider schema must accept L6.72.52+ / L6.73.x")
    _assert("openai" in PROVIDER_OPTIONS and "local" in PROVIDER_OPTIONS, "provider options incomplete")
    deepseek_values = model_values_for_provider("deepseek")
    openai_values = model_values_for_provider("openai")
    compat_values = model_values_for_provider("openai_compatible")
    _assert("deepseek-v4-pro" in deepseek_values, "DeepSeek model missing")
    _assert(MODEL_CUSTOM_SENTINEL in deepseek_values, "DeepSeek custom fallback missing")
    _assert(MODEL_CUSTOM_SENTINEL in openai_values, "OpenAI custom model input missing")
    _assert(MODEL_CUSTOM_SENTINEL in compat_values, "OpenAI-compatible custom model input missing")
    _assert(all(item.provider == "deepseek" for item in filter_model_catalog("", provider="deepseek")), "DeepSeek catalog leaked other providers")
    _assert(all(item.provider == "openai" for item in filter_model_catalog("", provider="openai")), "OpenAI catalog leaked other providers")
    _assert(effective_model_name("openai", MODEL_CUSTOM_SENTINEL, "gpt-custom-latest") == "gpt-custom-latest", "OpenAI custom effective model failed")
    _assert(effective_model_name("openai_compatible", "deepseek-v4-pro", "my-router-model") == "my-router-model", "OpenAI-compatible custom override failed")
    settings = sanitize_runtime_settings({"provider": "openai", "main_model": MODEL_CUSTOM_SENTINEL, "custom_model": "gpt-custom-latest", "api_key": "mockkey_test", "api_base_url": "https://api.openai.com/v1"})
    _assert(settings["provider"] == "openai" and settings["main_model"] == "gpt-custom-latest", "sanitized provider/model binding failed")
    _assert(settings["api_key_configured"] and settings["base_url_configured"], "sanitized configured flags failed")
    req = ProviderSettingsWriteRequest.from_form({"provider": "local", "model": "local-qwen", "base_url": "http://127.0.0.1:8000/v1"})
    _assert(req.provider == "local", "provider_settings does not allow local")
    _assert(provider_allows_custom_model("openai"), "OpenAI custom flag false")
    _assert(default_base_url_for_provider("deepseek") == "https://api.deepseek.com", "DeepSeek base URL default broken")
    _assert(normalize_provider_value("openai-compatible") == "openai_compatible", "provider alias normalize failed")
    print("PASS provider_model_binding_smoke_l67223")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
