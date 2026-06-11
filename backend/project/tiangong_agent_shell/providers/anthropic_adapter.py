"""L6.72.58 Anthropic / Claude / Fable native adapter。"""

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


class AnthropicNativeAdapter:
    provider = "anthropic"

    def chat(self, prompt: Any, config: ModelConfig) -> ChatResult:
        if not config.has_real_api_key:
            raise ModelClientError("缺少 API Key：Anthropic/Claude/Fable native adapter 需要 API Key。", error_kind="auth_error", provider=self.provider)
        if not config.model:
            raise ModelClientError("缺少模型名：请设置 Claude/Fable 模型名。", error_kind="model_not_found", provider=self.provider)
        envelope = ensure_compiled_prompt_envelope(prompt)
        system, messages = _split_system_and_messages(envelope.as_messages())
        payload = {
            "model": config.model,
            "max_tokens": 4096,
            "messages": messages,
        }
        if system:
            payload["system"] = system
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        base = (config.base_url or "https://api.anthropic.com").rstrip("/")
        url = base if base.endswith("/messages") else f"{base}/v1/messages"
        request = urllib.request.Request(
            url=url,
            data=body,
            method="POST",
            headers={
                "x-api-key": config.api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "X-Tiangong-Prompt-Id": envelope.compiled_prompt_id,
                "X-Tiangong-Prompt-Integrator": envelope.prompt_integrator_version,
            },
        )
        try:
            with urlopen_with_policy(request, timeout=config.timeout, allow_loopback_http=False, purpose="model_provider") as response:
                raw_bytes = response.read()
        except urllib.error.HTTPError as exc:
            detail = _read_http_error_detail(exc, config.api_key)
            error = classify_provider_error(exc, provider=self.provider, status_code=exc.code, detail=detail, api_key=config.api_key)
            raise ModelClientError(error.user_message, **to_model_client_error_kwargs(error)) from exc
        except NetworkPolicyError as exc:
            error = classify_provider_error(exc, provider=self.provider, detail=str(exc), api_key=config.api_key)
            raise ModelClientError("网络策略拒绝：Anthropic native adapter 必须使用 HTTPS。", **to_model_client_error_kwargs(error)) from exc
        except UnicodeEncodeError as exc:
            error = classify_provider_error(exc, provider=self.provider, detail=str(exc), api_key=config.api_key)
            raise ModelClientError(error.user_message, **to_model_client_error_kwargs(error)) from exc
        except (urllib.error.URLError, socket.timeout, TimeoutError) as exc:
            error = classify_provider_error(exc, provider=self.provider, detail=str(exc), api_key=config.api_key)
            raise ModelClientError(error.user_message, **to_model_client_error_kwargs(error)) from exc
        try:
            data = json.loads(raw_bytes.decode("utf-8"))
            parts = data.get("content") or []
            content = "".join(str(part.get("text", "")) for part in parts if isinstance(part, dict) and part.get("type") in {"text", None})
        except (UnicodeDecodeError, json.JSONDecodeError, TypeError) as exc:
            error = classify_provider_error(exc, provider=self.provider, detail=str(exc), api_key=config.api_key)
            raise ModelClientError(error.user_message, **to_model_client_error_kwargs(error)) from exc
        if not content:
            error = classify_provider_error(None, provider=self.provider, detail="empty anthropic content", api_key=config.api_key)
            raise ModelClientError(error.user_message, **to_model_client_error_kwargs(error))
        raw = dict(data)
        raw.setdefault("tiangong_prompt", envelope.public_dict())
        return ChatResult(content=content, provider=self.provider, model=config.model, raw=raw)


def _split_system_and_messages(messages: list[dict[str, str]]) -> tuple[str, list[dict[str, str]]]:
    system_parts: list[str] = []
    out: list[dict[str, str]] = []
    for item in messages:
        role = item.get("role") or "user"
        content = str(item.get("content") or "")
        if role == "system":
            system_parts.append(content)
        elif role in {"user", "assistant"}:
            out.append({"role": role, "content": content})
        else:
            out.append({"role": "user", "content": content})
    if not out:
        out.append({"role": "user", "content": "继续。"})
    return "\n\n".join(system_parts), out


def _read_http_error_detail(exc: urllib.error.HTTPError, api_key: str) -> str:
    try:
        raw = exc.read().decode("utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        raw = str(exc)
    return redact_text(raw, [api_key])
