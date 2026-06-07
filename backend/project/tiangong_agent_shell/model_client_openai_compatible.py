"""OpenAI-compatible 最小非流式模型客户端。"""

from __future__ import annotations

import json
import socket
import urllib.error
import urllib.request

from .config_loader import ModelConfig
from .errors import ModelClientError
from .model_client_port import ChatResult
from .safe_logging import redact_text


class OpenAICompatibleModelClient:
    provider = "openai_compatible"

    def chat(self, messages: list[dict[str, str]], config: ModelConfig) -> ChatResult:
        _validate_config(config)
        url = _chat_completions_url(config.base_url)
        payload = {
            "model": config.model,
            "messages": messages,
            "stream": False,
        }
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(
            url=url,
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {config.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=config.timeout) as response:  # nosec B310: user-provided endpoint by design
                raw_bytes = response.read()
        except urllib.error.HTTPError as exc:
            detail = _read_http_error_detail(exc, config.api_key)
            raise ModelClientError(_http_user_message(exc.code), status_code=exc.code, detail=detail) from exc
        except urllib.error.URLError as exc:
            raise ModelClientError("网络连接失败：请检查 Base URL、网络代理或服务商状态。", detail=redact_text(str(exc), [config.api_key])) from exc
        except socket.timeout as exc:
            raise ModelClientError("模型请求超时：请检查网络或调大 timeout。", detail=str(exc)) from exc
        except TimeoutError as exc:
            raise ModelClientError("模型请求超时：请检查网络或调大 timeout。", detail=str(exc)) from exc

        try:
            data = json.loads(raw_bytes.decode("utf-8"))
            content = data["choices"][0]["message"]["content"]
        except (UnicodeDecodeError, json.JSONDecodeError, KeyError, IndexError, TypeError) as exc:
            raise ModelClientError("模型返回格式异常：无法从 choices[0].message.content 解析文本。", detail=str(exc)) from exc
        return ChatResult(content=str(content), provider=self.provider, model=config.model, raw=data)


def _validate_config(config: ModelConfig) -> None:
    if not config.base_url:
        raise ModelClientError("缺少 Base URL：请设置 TIANGONG_BASE_URL 或 --base-url。")
    if not config.has_real_api_key:
        raise ModelClientError("缺少 API Key：请设置 TIANGONG_API_KEY 或 --api-key；也可使用 --mock 验证启动链。")
    if not config.model:
        raise ModelClientError("缺少模型名：请设置 TIANGONG_MODEL 或 --model。")


def _chat_completions_url(base_url: str) -> str:
    base = base_url.rstrip("/")
    if base.endswith("/chat/completions"):
        return base
    return f"{base}/chat/completions"


def _http_user_message(status_code: int) -> str:
    if status_code in {401, 403}:
        return "API Key 可能错误或无权限：请检查密钥、余额和服务商权限。"
    if status_code == 404:
        return "Base URL 或模型名可能错误：请检查服务商地址和 model。"
    if status_code == 429:
        return "请求被限流或余额不足：请稍后重试或检查账户额度。"
    if 500 <= status_code <= 599:
        return "服务商接口暂时异常：请稍后重试或切换模型。"
    return f"模型接口返回 HTTP {status_code}。"


def _read_http_error_detail(exc: urllib.error.HTTPError, api_key: str) -> str:
    try:
        raw = exc.read().decode("utf-8", errors="replace")
    except Exception:  # noqa: BLE001 - best effort detail only
        raw = str(exc)
    return redact_text(raw, [api_key])
