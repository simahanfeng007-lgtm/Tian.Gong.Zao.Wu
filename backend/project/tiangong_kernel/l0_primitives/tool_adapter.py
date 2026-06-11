"""L0 工具与适配器引用事实语言原语。

本模块在 L0 中的职责：定义工具、适配器、版本和状态的引用事实。
本模块只表达：工具引用、适配器引用、类别、状态和版本引用。
本模块明确不做：工具执行、schema 校验、认证、限流、沙箱绑定或具体实现路径。
禁止事项：不得调用工具，不得绑定外部协议，不得执行文件、终端、网络或数据库操作。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .identity import RefId, TypedRef


class ToolKind(str, Enum):
    """工具类别：只表达工具用途类型；UNKNOWN 表示类别未知。"""
    OBSERVATION="observation"; READ="read"; WRITE="write"; EXECUTION="execution"; COMMUNICATION="communication"; SEARCH="search"; COMPUTATION="computation"; RECOVERY="recovery"; SAFETY="safety"; UNKNOWN="unknown"
class AdapterKind(str, Enum):
    """适配器类别：只表达外部连接边界类型；UNKNOWN 表示类别未知。"""
    MODEL_ADAPTER="model_adapter"; TOOL_ADAPTER="tool_adapter"; STORAGE_ADAPTER="storage_adapter"; NETWORK_ADAPTER="network_adapter"; SANDBOX_ADAPTER="sandbox_adapter"; PLUGIN_ADAPTER="plugin_adapter"; GATEWAY_ADAPTER="gateway_adapter"; MCP_ADAPTER="mcp_adapter"; UNKNOWN="unknown"
class ToolState(str, Enum):
    """工具状态：只表达工具引用生命周期；UNKNOWN 表示状态未知。"""
    DISCOVERED="discovered"; REGISTERED="registered"; AVAILABLE="available"; LEASED="leased"; ACTIVE="active"; DEGRADED="degraded"; DISABLED="disabled"; QUARANTINED="quarantined"; REVOKED="revoked"; ARCHIVED="archived"; UNKNOWN="unknown"
@dataclass(frozen=True, slots=True)
class ToolVersionRef:
    """工具版本引用。作用：表达工具版本引用；所属 L0 边界：只保存 tool_version_id 与 tool_ref；不能加载或校验工具实现。"""
    value: RefId; tool_ref: TypedRef|None=None; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("ToolVersionRef.schema_version cannot be empty")
@dataclass(frozen=True, slots=True)
class AdapterVersionRef:
    """适配器版本引用。作用：表达适配器版本引用；所属 L0 边界：只保存 adapter_version_id 与 adapter_ref；不能加载适配器。"""
    value: RefId; adapter_ref: TypedRef|None=None; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("AdapterVersionRef.schema_version cannot be empty")
@dataclass(frozen=True, slots=True)
class ToolRef:
    """工具引用。作用：表达用于执行或观察的工具引用；所属 L0 边界：只保存 tool_id、kind、state、version_ref；不能执行工具或保存真实句柄。"""
    value: RefId; kind: ToolKind=ToolKind.UNKNOWN; state: ToolState=ToolState.UNKNOWN; version_ref: ToolVersionRef|None=None; owner_ref: TypedRef|None=None; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("ToolRef.schema_version cannot be empty")
@dataclass(frozen=True, slots=True)
class AdapterRef:
    """适配器引用。作用：表达连接真实模型、工具、存储、网络、系统资源或外部协议的适配器引用；所属 L0 边界：只保存 adapter_id、kind、state、version_ref；不能执行适配。"""
    value: RefId; kind: AdapterKind=AdapterKind.UNKNOWN; state: ToolState=ToolState.UNKNOWN; version_ref: AdapterVersionRef|None=None; boundary_ref: TypedRef|None=None; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("AdapterRef.schema_version cannot be empty")
