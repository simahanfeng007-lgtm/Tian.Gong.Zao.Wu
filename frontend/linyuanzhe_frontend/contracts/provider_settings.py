from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, Mapping

from .runtime_snapshot import digest_text, safe_text
from .sse_events import PROVIDER_SETTINGS_ENDPOINT


PROVIDER_SETTINGS_WRITE_CONTRACT_VERSION = "tiangong.l6_57.provider_settings_write.v1"
ALLOWED_PROVIDER_VALUES = {"deepseek", "qwen", "zhipu", "openai", "custom"}
WRITE_ONLY_FIELDS = ("api_key", "base_url")


@dataclass(frozen=True)
class ProviderSettingsWriteRequest:
    """Write-only Provider configuration request for Runtime.

    Raw ``api_key`` and ``base_url`` may exist only inside the outbound Runtime
    request body. Public/UI/report projections must use ``to_public_dict`` and
    must never contain these raw write-only values.
    """

    provider: str
    model: str
    api_key: str = ""
    base_url: str = ""
    timeout: float = 30.0
    stream: bool = True
    frontend_contract: str = PROVIDER_SETTINGS_WRITE_CONTRACT_VERSION
    endpoint: str = PROVIDER_SETTINGS_ENDPOINT
    no_frontend_provider_call: bool = True
    no_frontend_tool_execution: bool = True
    write_only_semantics: bool = True

    @classmethod
    def from_form(cls, raw: Mapping[str, Any]) -> "ProviderSettingsWriteRequest":
        provider = safe_text(raw.get("provider", "deepseek"), 40).lower() or "deepseek"
        if provider not in ALLOWED_PROVIDER_VALUES:
            provider = "custom"
        model = safe_text(raw.get("model") or raw.get("main_model") or raw.get("model_id") or "deepseek-reasoner", 100)
        api_key = "" if raw.get("api_key") is None else str(raw.get("api_key") or "")
        base_url = "" if raw.get("base_url") is None else str(raw.get("base_url") or raw.get("api_base_url") or "")
        if not base_url and raw.get("api_base_url") is not None:
            base_url = str(raw.get("api_base_url") or "")
        try:
            timeout = float(raw.get("timeout", 30.0) or 30.0)
        except (TypeError, ValueError):
            timeout = 30.0
        timeout = max(1.0, min(300.0, timeout))
        return cls(
            provider=provider,
            model=model,
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            stream=bool(raw.get("stream", True)),
        )

    @property
    def api_key_configured(self) -> bool:
        return bool(self.api_key.strip())

    @property
    def base_url_configured(self) -> bool:
        return bool(self.base_url.strip())

    def to_runtime_payload(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "frontend_contract": self.frontend_contract,
            "endpoint": self.endpoint,
            "provider": self.provider,
            "model": self.model,
            "timeout": self.timeout,
            "stream": self.stream,
            "write_only_fields": list(WRITE_ONLY_FIELDS),
            "no_frontend_provider_call": self.no_frontend_provider_call,
            "no_frontend_tool_execution": self.no_frontend_tool_execution,
            "write_only_semantics": self.write_only_semantics,
        }
        if self.api_key_configured:
            payload["api_key"] = self.api_key
        if self.base_url_configured:
            payload["base_url"] = self.base_url
        return payload

    def to_public_dict(self) -> Dict[str, Any]:
        return {
            "frontend_contract": self.frontend_contract,
            "endpoint": self.endpoint,
            "provider": self.provider,
            "model": self.model,
            "api_key_configured": self.api_key_configured,
            "api_key_digest": digest_text(self.api_key, 16) if self.api_key_configured else "",
            "base_url_configured": self.base_url_configured,
            "base_url_digest": digest_text(self.base_url, 16) if self.base_url_configured else "",
            "timeout": self.timeout,
            "stream": self.stream,
            "raw_api_key_persisted": False,
            "raw_base_url_persisted": False,
            "no_frontend_provider_call": self.no_frontend_provider_call,
            "no_frontend_tool_execution": self.no_frontend_tool_execution,
            "write_only_semantics": self.write_only_semantics,
        }


@dataclass(frozen=True)
class ProviderSettingsWriteResult:
    """Sanitized Provider settings write acknowledgement from Runtime."""

    status: str = "idle"
    provider: str = ""
    model: str = ""
    api_key_configured: bool = False
    api_key_digest: str = ""
    base_url_configured: bool = False
    base_url_digest: str = ""
    config_error_code: str = ""
    message: str = ""
    audit_id: str = ""
    requires_restart: bool = False
    frontend_contract: str = PROVIDER_SETTINGS_WRITE_CONTRACT_VERSION
    endpoint: str = PROVIDER_SETTINGS_ENDPOINT
    raw_api_key_persisted: bool = False
    raw_base_url_persisted: bool = False

    @classmethod
    def from_runtime_response(cls, data: Mapping[str, Any]) -> "ProviderSettingsWriteResult":
        payload = data.get("payload", data)
        if not isinstance(payload, Mapping):
            payload = {}
        return cls(
            status=safe_text(payload.get("status", "submitted"), 40),
            provider=safe_text(payload.get("provider", ""), 40),
            model=safe_text(payload.get("model", payload.get("main_model", "")), 100),
            api_key_configured=bool(payload.get("api_key_configured", False)),
            api_key_digest=safe_text(payload.get("api_key_digest", ""), 32),
            base_url_configured=bool(payload.get("base_url_configured", False)),
            base_url_digest=safe_text(payload.get("base_url_digest", ""), 32),
            config_error_code=safe_text(payload.get("config_error_code", payload.get("error_code", "")), 80),
            message=safe_text(payload.get("message", ""), 220),
            audit_id=safe_text(payload.get("audit_id", payload.get("audit_ref", "")), 80),
            requires_restart=bool(payload.get("requires_restart", False)),
        )

    @classmethod
    def from_error(cls, error: Any, *, provider: str = "", model: str = "") -> "ProviderSettingsWriteResult":
        return cls(
            status="error",
            provider=safe_text(provider, 40),
            model=safe_text(model, 100),
            config_error_code="frontend_submit_failed",
            message=safe_text(error, 220),
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def provider_settings_write_policy() -> Dict[str, Any]:
    return {
        "contract_version": PROVIDER_SETTINGS_WRITE_CONTRACT_VERSION,
        "endpoint": PROVIDER_SETTINGS_ENDPOINT,
        "method": "POST",
        "write_only_fields": list(WRITE_ONLY_FIELDS),
        "frontend_may_submit_request": True,
        "frontend_may_display_digest": True,
        "frontend_must_not_persist_raw_api_key": True,
        "frontend_must_not_persist_raw_base_url": True,
        "frontend_must_not_call_provider_sdk": True,
        "frontend_must_not_execute_tools": True,
        "runtime_owns_credential_storage": True,
    }
