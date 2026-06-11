"""密钥脱敏与安全显示工具。"""

from __future__ import annotations

from collections.abc import Mapping
import hashlib
import re
from typing import Any

SECRET_KEYS = {"api_key", "apikey", "authorization", "token", "secret", "password"}
ENDPOINT_KEYS = {"base_url", "endpoint", "endpoint_url", "provider_base_url", "url"}


def redact_secret(secret: str | None) -> str:
    """返回密钥摘要态，不展示前缀、后缀或任何原文片段。"""
    if not secret:
        return "<未配置>"
    value = str(secret)
    if value in {"PLEASE_SET_YOUR_API_KEY", "YOUR_API_KEY", "example"}:
        return "<示例占位>"
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]
    return f"<已配置:digest:{digest}>"


def redact_endpoint(endpoint: str | None) -> str:
    """返回 endpoint/base_url 的摘要态，避免状态页暴露真实服务地址。"""
    if not endpoint:
        return "<未配置>"
    value = str(endpoint).strip()
    if not value:
        return "<未配置>"
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]
    return f"<已配置:digest:{digest}>"


_OPENAI_LIKE_KEY_RE = re.compile(r"\bmockkey_[A-Za-z0-9][A-Za-z0-9_\-]{7,}\b")
_BEARER_VALUE_RE = re.compile(r"(?i)\b(authorization)\b\s*[:=]\s*bearer\s+([^\s,;]+)")
_SECRET_VALUE_RE = re.compile(r"(?i)\b(api[_-]?key|apikey|token|secret|password|credential)\b\s*[:=]\s*([^\s,;]+)")
_ENDPOINT_VALUE_RE = re.compile(r"(?i)\b(base_url|endpoint|endpoint_url|provider_base_url)\b\s*[:=]\s*([^\s,;]+)")


def redact_text(text: str, secrets: list[str | None] | tuple[str | None, ...] = ()) -> str:
    """从任意文本中替换已知密钥与显式标注的 endpoint。

    L6.49.5：极端压测发现 ``external_context_hint`` 可能携带
    ``api_key=...`` / ``token=...`` / ``base_url=...`` 这类片段。
    这里不屏蔽普通 URL 或普通正文，只对明确带敏感字段名的值、Bearer token、
    以及 OpenAI/DeepSeek 常见 ``mockkey_`` 形态密钥做摘要态替换。
    """
    result = str(text)
    for secret in secrets:
        if secret and secret in result:
            result = result.replace(secret, redact_secret(secret))

    def _replace_bearer(match: re.Match[str]) -> str:
        return f"{match.group(1)}: Bearer {redact_secret(match.group(2))}"

    def _replace_secret(match: re.Match[str]) -> str:
        return f"{match.group(1)}={redact_secret(match.group(2))}"

    def _replace_endpoint(match: re.Match[str]) -> str:
        return f"{match.group(1)}={redact_endpoint(match.group(2))}"

    result = _BEARER_VALUE_RE.sub(_replace_bearer, result)
    result = _SECRET_VALUE_RE.sub(_replace_secret, result)
    result = _ENDPOINT_VALUE_RE.sub(_replace_endpoint, result)
    result = _OPENAI_LIKE_KEY_RE.sub(lambda m: redact_secret(m.group(0)), result)
    return result


def sanitize_mapping(mapping: Mapping[str, Any]) -> dict[str, Any]:
    """递归脱敏配置映射。"""
    sanitized: dict[str, Any] = {}
    for key, value in mapping.items():
        key_lower = str(key).lower()
        if key_lower in SECRET_KEYS:
            sanitized[key] = redact_secret(str(value) if value is not None else None)
        elif key_lower in ENDPOINT_KEYS:
            sanitized[key] = redact_endpoint(str(value) if value is not None else None)
        elif isinstance(value, Mapping):
            sanitized[key] = sanitize_mapping(value)
        else:
            sanitized[key] = value
    return sanitized


def has_unredacted_secret(text: str, secret: str | None) -> bool:
    """测试辅助：判断文本中是否包含未脱敏密钥。"""
    return bool(secret) and secret not in {"PLEASE_SET_YOUR_API_KEY"} and secret in text
