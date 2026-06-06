"""L1 通信与交接信封端口声明。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef
from tiangong_kernel.l0_primitives.trace import TraceContext

from .port_result import PortResult


@dataclass(frozen=True, slots=True)
class MessageEnvelopeSubmitRequest:
    """消息信封提交请求，承载发送方、接收方、范围、权限和审计引用。"""

    request_ref: TypedRef
    message_envelope_ref: TypedRef
    sender_ref: TypedRef
    receiver_ref: TypedRef
    conversation_ref: TypedRef | None = None
    scope_ref: TypedRef | None = None
    authority_ref: TypedRef | None = None
    provenance_ref: TypedRef | None = None
    audit_ref: TypedRef | None = None
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class MessageEnvelopeSubmitResponse:
    """消息信封提交响应，返回消息信封引用。"""

    response_ref: TypedRef
    message_envelope_ref: TypedRef
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class HandoffEnvelopeSubmitRequest:
    """交接信封提交请求，承载交接双方、责任、租约、策略和证据引用。"""

    request_ref: TypedRef
    handoff_ref: TypedRef
    source_message_envelope_ref: TypedRef
    from_actor_ref: TypedRef
    to_actor_ref: TypedRef
    conversation_ref: TypedRef
    scope_ref: TypedRef | None = None
    authority_ref: TypedRef | None = None
    provenance_ref: TypedRef | None = None
    responsibility_ref: TypedRef | None = None
    lease_ref: TypedRef | None = None
    policy_ref: TypedRef | None = None
    audit_ref: TypedRef | None = None
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class HandoffEnvelopeSubmitResponse:
    """交接信封提交响应，返回交接回执引用。"""

    response_ref: TypedRef
    handoff_ref: TypedRef
    receipt_ref: TypedRef | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ActorCommunicationRequest:
    """参与者通信请求，承载双方参与者和消息信封引用。"""

    request_ref: TypedRef
    from_actor_ref: TypedRef
    to_actor_ref: TypedRef
    message_envelope_ref: TypedRef
    conversation_ref: TypedRef | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class ActorCommunicationResponse:
    """参与者通信响应，返回消息信封引用。"""

    response_ref: TypedRef
    message_envelope_ref: TypedRef
    schema_version: str = "0.1"


class MessageEnvelopePort(ABC):
    """消息信封端口，只声明信封提交契约。"""

    @abstractmethod
    def submit_message_envelope(self, request: MessageEnvelopeSubmitRequest, trace: TraceContext) -> PortResult[MessageEnvelopeSubmitResponse]:
        raise NotImplementedError


class ActorHandoffPort(ABC):
    """参与者交接端口，只声明交接信封契约。"""

    @abstractmethod
    def submit_handoff_envelope(self, request: HandoffEnvelopeSubmitRequest, trace: TraceContext) -> PortResult[HandoffEnvelopeSubmitResponse]:
        raise NotImplementedError


class MultiActorCommunicationPort(ABC):
    """多参与者通信端口，只声明通信协作契约。"""

    @abstractmethod
    def submit_actor_communication(self, request: ActorCommunicationRequest, trace: TraceContext) -> PortResult[ActorCommunicationResponse]:
        raise NotImplementedError
