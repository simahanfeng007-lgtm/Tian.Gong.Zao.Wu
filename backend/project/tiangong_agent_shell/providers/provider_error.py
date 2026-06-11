"""L6.72.58 Provider 统一错误分类。

本模块只做 Provider 错误语义归一与脱敏，不触发重试、不执行工具、不读取密钥。
各 Provider adapter 将 HTTP/网络/格式异常转换为统一 ProviderError，再由
ModelClientError 暴露给 Runtime/Planner。这样不同服务商的错误不会再混成
普通 provider_error，也不会把原始堆栈刷到会话区。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any
import socket
import urllib.error

from tiangong_agent_shell.safe_logging import redact_text


class ProviderErrorKind(StrEnum):
    AUTH_ERROR = "auth_error"
    MODEL_NOT_FOUND = "model_not_found"
    RATE_LIMITED = "rate_limited"
    CONTEXT_OVERFLOW = "context_overflow"
    INVALID_JSON = "invalid_json"
    REFUSAL = "refusal"
    TIMEOUT = "timeout"
    SERVER_ERROR = "server_error"
    UNSUPPORTED_FEATURE = "unsupported_feature"


_RETRYABLE = {
    ProviderErrorKind.RATE_LIMITED,
    ProviderErrorKind.TIMEOUT,
    ProviderErrorKind.SERVER_ERROR,
}


@dataclass(frozen=True)
class ProviderError:
    kind: ProviderErrorKind
    user_message: str
    provider: str = "unknown"
    status_code: int | None = None
    retryable: bool = False
    detail: str = ""

    def public_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind.value,
            "provider": self.provider,
            "status_code": self.status_code,
            "retryable": self.retryable,
            "user_message": self.user_message,
            "detail_preview": redact_text(self.detail)[:500],
            "storage_boundary": {
                "no_api_key": True,
                "no_raw_prompt": True,
                "no_plain_endpoint": True,
                "summary_only": True,
            },
        }


def classify_provider_error(
    exc: BaseException | None = None,
    *,
    provider: str = "unknown",
    status_code: int | None = None,
    detail: str = "",
    api_key: str = "",
) -> ProviderError:
    """把不同异常归一为 ProviderError。

    分类优先级：HTTP status -> 文本特征 -> Python 异常类型。输出 detail 会脱敏。
    """
    raw = " ".join(
        part
        for part in (
            str(detail or ""),
            str(getattr(exc, "user_message", "") or ""),
            str(getattr(exc, "detail", "") or ""),
            str(exc or ""),
        )
        if part
    )
    clean_detail = redact_text(raw, [api_key])[:2000]
    code = status_code if status_code is not None else getattr(exc, "code", None)
    try:
        code = int(code) if code is not None else None
    except (TypeError, ValueError):
        code = None
    text = clean_detail.lower()

    if code in {401, 403}:
        kind = ProviderErrorKind.AUTH_ERROR
    elif code == 404:
        kind = ProviderErrorKind.MODEL_NOT_FOUND
    elif code == 429:
        kind = ProviderErrorKind.RATE_LIMITED
    elif code is not None and 500 <= code <= 599:
        kind = ProviderErrorKind.SERVER_ERROR
    elif isinstance(exc, UnicodeEncodeError) or "unicodeencodeerror" in text or "codec can't encode" in text:
        kind = ProviderErrorKind.UNSUPPORTED_FEATURE
    elif _looks_like_timeout(exc, text):
        kind = ProviderErrorKind.TIMEOUT
    elif _contains_any(text, ("context length", "maximum context", "too many tokens", "token limit", "context_overflow", "上下文", "超出上下文")):
        kind = ProviderErrorKind.CONTEXT_OVERFLOW
    elif _contains_any(text, ("invalid json", "json_decode", "malformed json", "not valid json", "返回格式异常")):
        kind = ProviderErrorKind.INVALID_JSON
    elif _contains_any(text, ("refusal", "refused", "safety", "policy", "blocked by", "拒绝")):
        kind = ProviderErrorKind.REFUSAL
    elif _contains_any(text, ("unsupported", "not supported", "unknown parameter", "不支持")):
        kind = ProviderErrorKind.UNSUPPORTED_FEATURE
    else:
        kind = ProviderErrorKind.SERVER_ERROR

    return ProviderError(
        kind=kind,
        user_message=_user_message_for_kind(kind),
        provider=str(provider or "unknown"),
        status_code=code,
        retryable=kind in _RETRYABLE,
        detail=clean_detail,
    )


def _contains_any(text: str, tokens: tuple[str, ...]) -> bool:
    return any(token in text for token in tokens)


def _looks_like_timeout(exc: BaseException | None, text: str) -> bool:
    return isinstance(exc, (socket.timeout, TimeoutError, TimeoutExceptionPlaceholder)) or "timed out" in text or "timeout" in text or "超时" in text


class TimeoutExceptionPlaceholder(Exception):
    """仅用于 isinstance 元组占位；不主动抛出。"""


def _user_message_for_kind(kind: ProviderErrorKind) -> str:
    if kind is ProviderErrorKind.AUTH_ERROR:
        return "Provider 鉴权失败：请检查 API Key、权限、余额或服务商控制台配置。"
    if kind is ProviderErrorKind.MODEL_NOT_FOUND:
        return "Provider 模型或地址不存在：请检查模型名、Base URL 或服务商路由。"
    if kind is ProviderErrorKind.RATE_LIMITED:
        return "Provider 限流或额度不足：可稍后重试、降低并发或切换模型。"
    if kind is ProviderErrorKind.CONTEXT_OVERFLOW:
        return "Provider 上下文超限：Runtime 将尝试压缩上下文后重试。"
    if kind is ProviderErrorKind.INVALID_JSON:
        return "Provider 返回格式异常：需要进入 short_json / choice_form 修复。"
    if kind is ProviderErrorKind.REFUSAL:
        return "Provider 拒绝了本轮请求：需要缩小任务、调整提示或改为可执行子任务。"
    if kind is ProviderErrorKind.TIMEOUT:
        return "Provider 请求超时：Runtime 可进入重试、回退或 provider_not_ready 报告。"
    if kind is ProviderErrorKind.UNSUPPORTED_FEATURE:
        return "Provider 请求编码或特性不支持：请检查 API Key、Base URL、模型名是否误填中文、全角符号、空格或不可见字符；必要时切换 adapter。"
    return "Provider 服务异常：请稍后重试或切换模型。"


def to_model_client_error_kwargs(error: ProviderError) -> dict[str, Any]:
    return {
        "status_code": error.status_code,
        "detail": error.detail,
        "error_kind": error.kind.value,
        "provider": error.provider,
        "retryable": error.retryable,
    }
