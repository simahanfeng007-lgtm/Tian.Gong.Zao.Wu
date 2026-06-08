"""工具执行桥。

L6.9 阶段只做外壳启动与对话闭环。真实工具执行默认禁用，
后续只能通过 RuntimeGovernedToolBridge 接入治理链。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class ToolExecutionMode(str, Enum):
    DISABLED = "disabled"
    DRY_RUN = "dry_run"
    RUNTIME_GOVERNED = "runtime_governed"


@dataclass(frozen=True)
class ToolBridgeResult:
    allowed: bool
    mode: ToolExecutionMode
    message: str
    payload: dict[str, Any] | None = None


class ToolBridge:
    """默认安全工具桥。"""

    def __init__(self, mode: str | ToolExecutionMode = ToolExecutionMode.RUNTIME_GOVERNED) -> None:
        self.mode = normalize_tool_mode(mode)
        self._capabilities: dict[str, bool] = {}

    def register_capability(self, name: str, enabled: bool) -> None:
        self._capabilities[str(name)] = bool(enabled)

    def capability_enabled(self, name: str) -> bool:
        return bool(self._capabilities.get(str(name), False))

    def public_capabilities(self) -> dict[str, bool]:
        return dict(sorted(self._capabilities.items()))

    def execute(self, tool_name: str, arguments: dict[str, Any] | None = None) -> ToolBridgeResult:
        if tool_name in {"write_file", "write_workspace_file"} and self._capabilities.get("write_file") is False:
            return ToolBridgeResult(
                allowed=False,
                mode=self.mode,
                message="当前 CLI 工作区未通过写入能力检测；写文件工具不可用。",
                payload={"tool_name": tool_name, "arguments": arguments or {}, "capability": "write_file"},
            )
        if self.mode is ToolExecutionMode.DISABLED:
            return ToolBridgeResult(
                allowed=False,
                mode=self.mode,
                message="工具执行默认禁用：L6.9 只开放最小对话启动闭环。",
            )
        if self.mode is ToolExecutionMode.DRY_RUN:
            return ToolBridgeResult(
                allowed=False,
                mode=self.mode,
                message="dry_run：已记录工具请求，但未执行真实工具。",
                payload={"tool_name": tool_name, "arguments": arguments or {}},
            )
        return ToolBridgeResult(
            allowed=False,
            mode=self.mode,
            message="runtime_governed 桥尚未接入；禁止绕过治理链执行工具。",
            payload={"tool_name": tool_name, "arguments": arguments or {}},
        )


def normalize_tool_mode(mode: str | ToolExecutionMode | None) -> ToolExecutionMode:
    if isinstance(mode, ToolExecutionMode):
        return mode
    value = (mode or ToolExecutionMode.DISABLED.value).strip().lower()
    aliases = {
        "disabled": ToolExecutionMode.DISABLED,
        "off": ToolExecutionMode.DISABLED,
        "false": ToolExecutionMode.DISABLED,
        "dryrun": ToolExecutionMode.DRY_RUN,
        "dry_run": ToolExecutionMode.DRY_RUN,
        "runtime": ToolExecutionMode.RUNTIME_GOVERNED,
        "runtime_governed": ToolExecutionMode.RUNTIME_GOVERNED,
    }
    return aliases.get(value, ToolExecutionMode.RUNTIME_GOVERNED)
