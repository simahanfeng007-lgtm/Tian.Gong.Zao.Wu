from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Mapping

from .runtime_snapshot import digest_text, safe_text
from .sse_events import PROVIDER_SETTINGS_ENDPOINT


PROVIDER_SETTINGS_WRITE_CONTRACT_VERSION = "tiangong.l6_57.provider_settings_write.v1"
ALLOWED_PROVIDER_VALUES = {"openai_compatible", "deepseek", "qwen", "zhipu", "openai", "custom"}
WRITE_ONLY_FIELDS = ("api_key", "base_url")


PROVIDER_ERROR_HINTS: Dict[str, tuple[str, str, str]] = {
    "gateway_unreachable": (
        "网关不可达",
        "检查 Tailscale / Base URL / 网关进程后，发送一条短消息复测",
        "无法连到 OpenAI-compatible 网关。优先检查 Tailscale 是否在线、Base URL 是否为 /v1 上游地址、网关进程是否启动。",
    ),
    "auth_failed": (
        "API Key 无效或未授权",
        "重新填写 API Key 后保存，再发送短消息复测",
        "Provider 返回鉴权失败。前端只显示错误类型，不回显 Key。",
    ),
    "model_not_found": (
        "模型不存在或无权限",
        "确认模型名与账号权限，必要时换成可用模型",
        "Provider 没有接受当前模型名，或当前 Key 无权调用该模型。",
    ),
    "provider_timeout": (
        "Provider 超时",
        "检查网络与网关负载，或提高 Runtime 超时后重试",
        "请求超时。可能是网关无响应、模型排队或链路质量不足。",
    ),
    "provider_rate_limited": (
        "Provider 限流",
        "降低频率或更换额度后重试",
        "Provider 返回限流或额度约束。",
    ),
    "provider_server_error": (
        "Provider 服务端错误",
        "稍后重试；若持续出现，检查网关日志",
        "Provider 或兼容网关返回 5xx 服务端错误。",
    ),
    "provider_runtime_error": (
        "Provider 联调失败",
        "查看脱敏错误摘要，修正配置后发送短消息复测",
        "真实模型链路失败，但前端未直接调用 Provider。",
    ),
}


def provider_error_user_hint(error_code: Any) -> tuple[str, str, str]:
    code = safe_text(error_code, 80) or "provider_runtime_error"
    return PROVIDER_ERROR_HINTS.get(code, PROVIDER_ERROR_HINTS["provider_runtime_error"])


@dataclass(frozen=True)
class ProviderReadinessProjection:
    """Digest-only Provider readiness projection for UI guidance.

    This object is derived from public Runtime /settings/provider projection. It
    intentionally contains no raw API key, Base URL, endpoint, token, or secret.
    """

    readiness: str
    label: str
    missing_fields: List[str]
    effective_backend_mode: str
    requested_backend_mode: str
    primary_action: str
    can_use_real_model: bool
    mock_mode: bool
    message: str
    config_error_code: str = ""
    severity: str = "info"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def provider_readiness_from_public_projection(public: Mapping[str, Any]) -> ProviderReadinessProjection:
    """Return a safe, user-facing Provider readiness summary.

    The function accepts only already-sanitized public fields. It must not be
    called with raw provider credentials. STEP31Q also interprets the local
    bridge's last real-provider smoke result, but still only from public/digest
    projection fields.
    """

    api_key_configured = bool(public.get("api_key_configured", False))
    base_url_configured = bool(public.get("base_url_configured", False))
    requested_mode = safe_text(public.get("requested_backend_mode", "auto"), 40) or "auto"
    effective_mode = safe_text(public.get("effective_backend_mode", "mock"), 40) or "mock"
    state = safe_text(public.get("provider_config_state", public.get("status", "idle")), 60)
    last_check_state = safe_text(public.get("last_provider_check_state", ""), 60)
    config_error_code = safe_text(public.get("last_provider_error_code") or public.get("config_error_code", ""), 80)
    missing: List[str] = []
    raw_missing = public.get("missing_fields")
    if isinstance(raw_missing, list):
        missing = [safe_text(item, 40) for item in raw_missing if safe_text(item, 40)]
    else:
        if not base_url_configured:
            missing.append("base_url")
        if not api_key_configured:
            missing.append("api_key")

    severity = "info"
    if last_check_state == "failed" or state in {"error", "rejected", "failed"}:
        label, primary_action, default_message = provider_error_user_hint(config_error_code)
        readiness = "error"
        can_use_real_model = False
        mock_mode = True
        severity = "error"
        detail = safe_text(public.get("last_provider_error_message") or public.get("message") or default_message, 260)
        message = f"{default_message} 脱敏摘要：{detail}" if detail and detail != default_message else default_message
    elif effective_mode == "provider" and not missing:
        readiness = "ready"
        label = "真实模型就绪"
        primary_action = "返回会话继续对话"
        can_use_real_model = True
        mock_mode = False
        severity = "ok"
        if last_check_state == "passed":
            message = "最近一次真实 Provider 联调通过；配置由 Runtime / 本地桥接托管，前端只显示 digest。"
        else:
            message = "Provider 配置已由 Runtime / 本地桥接托管；发送一条短消息即可完成真实链路联调。"
    elif requested_mode == "mock":
        readiness = "forced_mock"
        label = "启动参数锁定 Mock"
        primary_action = "用 auto/provider 模式重启桌面端"
        can_use_real_model = False
        mock_mode = True
        severity = "warning"
        message = "当前启动参数为 mock，即使已保存配置也不会走真实模型。"
    elif missing:
        readiness = "missing_credentials"
        label = "缺 Provider 配置"
        primary_action = "填写 Base URL 与 API Key 后保存"
        can_use_real_model = False
        mock_mode = True
        severity = "warning"
        cn = {"base_url": "Base URL", "api_key": "API Key"}
        message = "缺少：" + "、".join(cn.get(item, item) for item in missing) + "；保存后本地桥接 auto 模式会切到 provider。"
    else:
        readiness = "saved_waiting_runtime"
        label = "配置已提交，等待 Runtime 确认"
        primary_action = "刷新快照或重新发送一条消息"
        can_use_real_model = False
        mock_mode = effective_mode != "provider"
        severity = "warning"
        message = safe_text(public.get("message", "配置已提交，但 Runtime 尚未返回 provider 模式。"), 220)

    return ProviderReadinessProjection(
        readiness=readiness,
        label=label,
        missing_fields=missing,
        effective_backend_mode=effective_mode,
        requested_backend_mode=requested_mode,
        primary_action=primary_action,
        can_use_real_model=can_use_real_model,
        mock_mode=mock_mode,
        message=message,
        config_error_code=config_error_code,
        severity=severity,
    )


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
        provider = safe_text(raw.get("provider", "openai_compatible"), 40).lower() or "openai_compatible"
        if provider not in ALLOWED_PROVIDER_VALUES:
            provider = "custom"
        model = safe_text(raw.get("model") or raw.get("main_model") or raw.get("model_id") or "deepseek-v4-pro", 100)
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
