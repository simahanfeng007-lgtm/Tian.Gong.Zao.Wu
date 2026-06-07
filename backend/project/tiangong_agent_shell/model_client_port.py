"""模型客户端端口定义。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .config_loader import ModelConfig


@dataclass(frozen=True)
class ChatResult:
    content: str
    provider: str
    model: str
    raw: dict | None = None


class ModelClientPort(Protocol):
    provider: str

    def chat(self, messages: list[dict[str, str]], config: ModelConfig) -> ChatResult:
        """发送对话消息并返回模型文本。"""
