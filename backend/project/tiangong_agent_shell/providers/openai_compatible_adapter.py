"""L6.72.58 OpenAI-compatible Provider adapter。

适用于 DeepSeek / Qwen / GLM / Minimax / Mimo 以及其他兼容
/v1/chat/completions 的服务。所有错误转为 ProviderError 分类后再抛出
ModelClientError，避免 Runtime 只能看到模糊 provider_error。
"""

from __future__ import annotations

import json
import socket
import urllib.error
import urllib.request
from typing import Any

from tiangong_agent_shell.config_loader import ModelConfig
from tiangong_agent_shell.errors import ModelClientError
from tiangong_agent_shell.model_client_port import ChatResult, ensure_compiled_prompt_envelope
from tiangong_agent_shell.network_policy import NetworkPolicyError, urlopen_with_policy
from tiangong_agent_shell.safe_logging import redact_text

from .provider_error import classify_provider_error, to_model_client_error_kwargs


class OpenAICompatibleAdapter:
    provider = "openai_compatible"

    def chat(self, prompt: Any, config: ModelConfig) -> ChatResult:
        _validate_config(config, provider=self.provider)
        try:
            envelope = ensure_compiled_prompt_envelope(prompt)
        except TypeError as exc:
            raise ModelClientError(str(exc), detail="ProviderClient boundary: compiled_prompt_envelope_required", error_kind="unsupported_feature", provider=self.provider) from exc
        url = _chat_completions_url(config.base_url)
        payload = {"model": config.model, "messages": envelope.as_messages(), "stream": False}
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(
            url=url,
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {config.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "X-Tiangong-Prompt-Id": envelope.compiled_prompt_id,
                "X-Tiangong-Prompt-Integrator": envelope.prompt_integrator_version,
            },
        )
        try:
            with urlopen_with_policy(request, timeout=config.timeout, allow_loopback_http=True, purpose="model_provider") as response:
                raw_bytes = response.read()
        except urllib.error.HTTPError as exc:
            detail = _read_http_error_detail(exc, config.api_key)
            error = classify_provider_error(exc, provider=_public_provider(config), status_code=exc.code, detail=detail, api_key=config.api_key)
            raise ModelClientError(error.user_message, **to_model_client_error_kwargs(error)) from exc
        except NetworkPolicyError as exc:
            error = classify_provider_error(exc, provider=_public_provider(config), detail=str(exc), api_key=config.api_key)
            raise ModelClientError("网络策略拒绝：远程模型接口必须使用 HTTPS；本机回环地址可使用 HTTP。", **to_model_client_error_kwargs(error)) from exc
        except UnicodeEncodeError as exc:
            error = classify_provider_error(exc, provider=_public_provider(config), detail=str(exc), api_key=config.api_key)
            raise ModelClientError(error.user_message, **to_model_client_error_kwargs(error)) from exc
        except (urllib.error.URLError, socket.timeout, TimeoutError) as exc:
            error = classify_provider_error(exc, provider=_public_provider(config), detail=str(exc), api_key=config.api_key)
            raise ModelClientError(error.user_message, **to_model_client_error_kwargs(error)) from exc

        try:
            data = json.loads(raw_bytes.decode("utf-8"))
            content = data["choices"][0]["message"]["content"]
        except (UnicodeDecodeError, json.JSONDecodeError, KeyError, IndexError, TypeError) as exc:
            error = classify_provider_error(exc, provider=_public_provider(config), detail=str(exc), api_key=config.api_key)
            raise ModelClientError(error.user_message, **to_model_client_error_kwargs(error)) from exc
        raw = dict(data)
        raw.setdefault("tiangong_prompt", envelope.public_dict())
        return ChatResult(content=str(content), provider=_public_provider(config), model=config.model, raw=raw)


def _validate_config(config: ModelConfig, *, provider: str) -> None:
    if not config.base_url:
        raise ModelClientError("缺少 Base URL：OpenAI-compatible Provider 必须设置服务商 Base URL。", error_kind="model_not_found", provider=provider)
    if not config.has_real_api_key:
        raise ModelClientError("缺少 API Key：请设置 TIANGONG_API_KEY 或 --api-key；桌面端请进入【设置】页保存模型接口配置。", error_kind="auth_error", provider=provider)
    if not config.model:
        raise ModelClientError("缺少模型名：请设置 TIANGONG_MODEL 或 --model。", error_kind="model_not_found", provider=provider)


def _chat_completions_url(base_url: str) -> str:
    base = str(base_url or "").rstrip("/")
    if base.endswith("/chat/completions"):
        return base
    if base.endswith("/v1"):
        return f"{base}/chat/completions"
    return f"{base}/chat/completions"


def _read_http_error_detail(exc: urllib.error.HTTPError, api_key: str) -> str:
    try:
        raw = exc.read().decode("utf-8", errors="replace")
    except Exception:  # noqa: BLE001 - best effort detail only
        raw = str(exc)
    return redact_text(raw, [api_key])


def _public_provider(config: ModelConfig) -> str:
    provider = str(getattr(config, "provider", "") or "").strip().lower()
    return provider or "openai_compatible"
