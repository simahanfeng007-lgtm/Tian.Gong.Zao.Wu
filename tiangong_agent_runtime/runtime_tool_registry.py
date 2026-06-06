"""运行时工具注册表。"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from .tool_invocation import ToolInvocation
from .tool_result import ToolResult
from .turn_context import TurnContext

ToolAdapter = Callable[[ToolInvocation, TurnContext], ToolResult]


@dataclass(frozen=True)
class ToolDescriptor:
    name: str
    description: str
    default_risk: str


class RuntimeToolRegistry:
    def __init__(self) -> None:
        self._adapters: dict[str, ToolAdapter] = {}
        self._descriptors: dict[str, ToolDescriptor] = {}

    def register(self, descriptor: ToolDescriptor, adapter: ToolAdapter) -> None:
        self._descriptors[descriptor.name] = descriptor
        self._adapters[descriptor.name] = adapter

    def get(self, tool_name: str) -> ToolAdapter | None:
        return self._adapters.get(tool_name)

    def describe(self) -> list[ToolDescriptor]:
        return [self._descriptors[name] for name in sorted(self._descriptors)]

    def names(self) -> list[str]:
        return sorted(self._adapters)
