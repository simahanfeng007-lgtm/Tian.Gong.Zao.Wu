"""L6.72.58 OpenAI native adapter。

使用 OpenAI Chat Completions 兼容端点，但作为 native adapter 管理默认端点、
ProviderError 分类和 PromptIntegrator envelope 边界。
"""

from __future__ import annotations

from typing import Any

from tiangong_agent_shell.config_loader import ModelConfig
from tiangong_agent_shell.model_client_port import ChatResult

from .openai_compatible_adapter import OpenAICompatibleAdapter


class OpenAINativeAdapter(OpenAICompatibleAdapter):
    provider = "openai"

    def chat(self, prompt: Any, config: ModelConfig) -> ChatResult:
        if not getattr(config, "base_url", ""):
            config = _with_base_url(config, "https://api.openai.com/v1")
        result = super().chat(prompt, config)
        return ChatResult(content=result.content, provider=self.provider, model=result.model, raw=result.raw)


def _with_base_url(config: ModelConfig, base_url: str) -> ModelConfig:
    return ModelConfig(
        provider=config.provider,
        base_url=base_url,
        api_key=config.api_key,
        model=config.model,
        timeout=config.timeout,
        stream=config.stream,
        tool_execution_mode=config.tool_execution_mode,
        planner_mode=config.planner_mode,
    )
