"""L0 通信外壳、通道、协议、会话和交接事实语言原语。

本模块在 L0 中的职责：定义消息外壳、逻辑通道、协议引用、会话链和交接引用事实。
本模块只表达：通信事实的引用、方向、投递状态、回复关系和责任转移引用。
本模块明确不做：网络传输、RPC、消息队列、路由、重试或协议实现。
禁止事项：不得发送消息，不得连接网络，不得实现 HTTP、WebSocket、JSON-RPC、MCP、A2A 或 IPC。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .identity import RefId, TypedRef


class MessageKind(str, Enum):
    """消息类别：只表达消息意图类型；UNKNOWN 表示类别未知。"""
    REQUEST="request"; RESPONSE="response"; EVENT_NOTIFICATION="event_notification"; COMMAND="command"; QUERY="query"; RESULT="result"; ERROR="error"; DELEGATION="delegation"; HANDOFF="handoff"; HEARTBEAT="heartbeat"; ACK="ack"; NACK="nack"; BROADCAST="broadcast"; UNKNOWN="unknown"
class MessageDirection(str, Enum):
    """消息方向：只表达流向关系；UNKNOWN 表示方向未知。"""
    INBOUND="inbound"; OUTBOUND="outbound"; INTERNAL="internal"; BIDIRECTIONAL="bidirectional"; UNKNOWN="unknown"
class ChannelKind(str, Enum):
    """通道类别：只表达逻辑通道归属；UNKNOWN 表示类别未知。"""
    INTERNAL="internal"; MODEL="model"; TOOL="tool"; PLUGIN="plugin"; USER="user"; SYSTEM="system"; NETWORK="network"; STORAGE="storage"; AUDIT="audit"; UNKNOWN="unknown"
class ProtocolKind(str, Enum):
    """协议类别：只表达消息遵循的协议引用类型；UNKNOWN 表示类别未知。"""
    INTERNAL="internal"; JSON_RPC="json_rpc"; MCP="mcp"; A2A="a2a"; HTTP="http"; WEBSOCKET="websocket"; CLI="cli"; IPC="ipc"; CUSTOM="custom"; UNKNOWN="unknown"
class DeliveryState(str, Enum):
    """投递状态：只表达消息外壳生命周期；UNKNOWN 表示状态未知。"""
    CREATED="created"; QUEUED="queued"; SENT="sent"; DELIVERED="delivered"; ACKED="acked"; FAILED="failed"; EXPIRED="expired"; CANCELLED="cancelled"; UNKNOWN="unknown"
@dataclass(frozen=True, slots=True)
class CommunicationRef:
    """通信引用。作用：表达一次通信事实的总引用；所属 L0 边界：只保存 communication_id、channel_ref、protocol_ref；不能传输消息。"""
    value: RefId; channel_ref: TypedRef|None=None; protocol_ref: TypedRef|None=None; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("CommunicationRef.schema_version cannot be empty")
@dataclass(frozen=True, slots=True)
class ChannelRef:
    """通道引用。作用：表达消息传输的逻辑通道引用；所属 L0 边界：只保存 channel_id、kind、scope_ref；不能打开连接。"""
    value: RefId; kind: ChannelKind=ChannelKind.UNKNOWN; scope_ref: TypedRef|None=None; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("ChannelRef.schema_version cannot be empty")
@dataclass(frozen=True, slots=True)
class ProtocolRef:
    """协议引用。作用：表达消息遵循的通信协议引用；所属 L0 边界：只保存 protocol_id、kind、version_ref；不能实现协议。"""
    value: RefId; kind: ProtocolKind=ProtocolKind.UNKNOWN; version_ref: TypedRef|None=None; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("ProtocolRef.schema_version cannot be empty")
@dataclass(frozen=True, slots=True)
class MessageEnvelopeRef:
    """消息外壳引用。作用：表达消息外壳事实，包括发送者、接收者、通道、协议、trace、scope、authority、provenance 和 payload 引用；所属 L0 边界：只保存 envelope_id 与引用字段；不能发送或路由消息。"""
    value: RefId; kind: MessageKind=MessageKind.UNKNOWN; direction: MessageDirection=MessageDirection.UNKNOWN; state: DeliveryState=DeliveryState.UNKNOWN; sender_ref: TypedRef|None=None; receiver_ref: TypedRef|None=None; channel_ref: ChannelRef|None=None; protocol_ref: ProtocolRef|None=None; payload_ref: TypedRef|None=None; trace_ref: TypedRef|None=None; scope_ref: TypedRef|None=None; authority_ref: TypedRef|None=None; provenance_ref: TypedRef|None=None; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("MessageEnvelopeRef.schema_version cannot be empty")
@dataclass(frozen=True, slots=True)
class ReplyToRef:
    """回复引用。作用：表达当前消息对另一消息的回复关系；所属 L0 边界：只保存 reply_to_id 与 message_ref；不能拉取上下文。"""
    value: RefId; message_ref: MessageEnvelopeRef|None=None; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("ReplyToRef.schema_version cannot be empty")
@dataclass(frozen=True, slots=True)
class ConversationRef:
    """会话链引用。作用：表达一组相关消息构成的交互链引用；所属 L0 边界：只保存 conversation_id 与 root_message_ref；不能存储完整消息列表。"""
    value: RefId; root_message_ref: MessageEnvelopeRef|None=None; participant_refs: tuple[TypedRef,...]=field(default_factory=tuple); schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("ConversationRef.schema_version cannot be empty")
@dataclass(frozen=True, slots=True)
class HandoffRef:
    """交接引用。作用：表达任务、上下文、责任或控制权从一个 Actor 转移到另一个 Actor 的事实引用；所属 L0 边界：只保存 handoff_id、from_ref、to_ref；不能执行交接流程。"""
    value: RefId; from_ref: TypedRef|None=None; to_ref: TypedRef|None=None; context_ref: TypedRef|None=None; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("HandoffRef.schema_version cannot be empty")
