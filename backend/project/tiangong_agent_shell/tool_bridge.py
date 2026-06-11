"""Legacy 外壳状态桥。

该模块来自 L6.9 最小外壳阶段，只保留“能力状态/禁用/干跑”提示职责。
真实工具执行主链是 RuntimeEntry -> PlannerExecutionController -> LongChainRunner
-> ExecutionSpine -> RuntimeToolRegistry -> Adapter。不得把本桥接成执行器，
否则会绕过 Runtime / QualityGate / Audit。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


LEGACY_STATUS_BRIDGE = True


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
    """L6.9 legacy status bridge；不是当前 Runtime 工具执行器。"""

    is_legacy_status_bridge = True

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
            message="legacy_status_bridge：ToolBridge 是 L6.9 外壳状态桥；真实工具执行必须走 RuntimeEntry -> PlannerExecutionController -> LongChainRunner -> ExecutionSpine -> RuntimeToolRegistry -> Adapter；禁止把此桥接成执行器。",
            payload={"tool_name": tool_name, "arguments": arguments or {}},
        )


def normalize_tool_mode(mode: str | ToolExecutionMode | None) -> ToolExecutionMode:
    if isinstance(mode, ToolExecutionMode):
        return mode
    value = (mode or ToolExecutionMode.RUNTIME_GOVERNED.value).strip().lower()
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
