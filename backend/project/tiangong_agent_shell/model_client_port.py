"""模型客户端端口定义。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol

from .config_loader import ModelConfig

PROMPT_INTEGRATOR_VERSION = "tiangong.l6_72_51.prompt_integrator.v1"
PROMPT_INTEGRATOR_SOURCE = "PromptIntegrator"


@dataclass(frozen=True)
class ChatResult:
    content: str
    provider: str
    model: str
    raw: dict | None = None


@dataclass(frozen=True)
class CompiledPromptEnvelope:
    """唯一允许进入 ProviderClient 的提示词载体。

    L6.72.51 冻结边界：Runtime / Planner / Bridge / Tool 都不能把裸
    ``messages`` 直接发给模型；它们只能提交结构化材料，由 PromptCompiler
    统一整合成此 envelope 后再交给 ProviderClient。
    """

    messages: tuple[dict[str, str], ...]
    compiled_prompt_id: str
    prompt_integrator_version: str = PROMPT_INTEGRATOR_VERSION
    source: str = PROMPT_INTEGRATOR_SOURCE
    phase: str = "execution"
    output_contract: str = "normal_chat"
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def as_messages(self) -> list[dict[str, str]]:
        return [dict(item) for item in self.messages]

    def public_dict(self) -> dict[str, Any]:
        return {
            "compiled_prompt_id": self.compiled_prompt_id,
            "prompt_integrator_version": self.prompt_integrator_version,
            "source": self.source,
            "phase": self.phase,
            "output_contract": self.output_contract,
            "message_count": len(self.messages),
            "metadata": dict(self.metadata or {}),
        }


def ensure_compiled_prompt_envelope(value: Any) -> CompiledPromptEnvelope:
    """Provider 层硬校验：拒绝裸 messages。"""
    if not isinstance(value, CompiledPromptEnvelope):
        raise TypeError("ProviderClient 拒绝裸 messages：必须传入 PromptIntegrator 生成的 CompiledPromptEnvelope。")
    if value.source != PROMPT_INTEGRATOR_SOURCE:
        raise TypeError("ProviderClient 拒绝非 PromptIntegrator 来源的 prompt envelope。")
    if value.prompt_integrator_version != PROMPT_INTEGRATOR_VERSION:
        raise TypeError("ProviderClient 拒绝未知 prompt_integrator_version。")
    if not value.compiled_prompt_id:
        raise TypeError("ProviderClient 拒绝缺少 compiled_prompt_id 的 prompt envelope。")
    if not value.messages:
        raise TypeError("ProviderClient 拒绝空 prompt envelope。")
    first_role = str(value.messages[0].get("role", ""))
    if first_role != "system":
        raise TypeError("ProviderClient 拒绝未由 PromptIntegrator 编译 system prompt 的 envelope。")
    return value


class ModelClientPort(Protocol):
    provider: str

    def chat(self, prompt: CompiledPromptEnvelope, config: ModelConfig) -> ChatResult:
        """发送已整合提示词并返回模型文本。"""
