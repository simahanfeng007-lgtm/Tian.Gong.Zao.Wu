"""L2 通信、交接与多参与者协作状态对象。"""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from .base_state import L2_STATE_SCHEMA_VERSION, L2StateMetadata
from .state_identity import L2StateIdentity
from .state_status import L2StateStatus


@dataclass(frozen=True, slots=True)
class CommunicationEnvelopeState:
    """通信信封状态，绑定收发方、通道、协议、会话、权限和证据引用。"""

    identity: L2StateIdentity
    status: L2StateStatus
    message_envelope_ref: TypedRef
    sender_ref: TypedRef | None = None
    receiver_ref: TypedRef | None = None
    channel_ref: TypedRef | None = None
    protocol_ref: TypedRef | None = None
    conversation_ref: TypedRef | None = None
    authority_ref: TypedRef | None = None
    provenance_ref: TypedRef | None = None
    audit_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION


@dataclass(frozen=True, slots=True)
class HandoffResponsibilityState:
    """交接责任状态，绑定交接双方、责任、范围、确认和返回引用。"""

    identity: L2StateIdentity
    status: L2StateStatus
    handoff_ref: TypedRef
    from_actor_ref: TypedRef | None = None
    to_actor_ref: TypedRef | None = None
    responsibility_ref: TypedRef | None = None
    scope_ref: TypedRef | None = None
    authority_ref: TypedRef | None = None
    provenance_ref: TypedRef | None = None
    ack_ref: TypedRef | None = None
    nack_ref: TypedRef | None = None
    result_return_ref: TypedRef | None = None
    failure_return_ref: TypedRef | None = None
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION


@dataclass(frozen=True, slots=True)
class ActorCollaborationState:
    """参与者协作状态，记录参与者、父参与者、工具租约和可见上下文引用。"""

    identity: L2StateIdentity
    status: L2StateStatus
    collaboration_ref: TypedRef
    participant_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    parent_actor_ref: TypedRef | None = None
    tool_lease_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    visible_context_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION


HandoffReceiptState = HandoffResponsibilityState
HandoffAckState = HandoffResponsibilityState
HandoffNackState = HandoffResponsibilityState
HandoffResultReturnState = HandoffResponsibilityState
HandoffFailureReturnState = HandoffResponsibilityState
ActorResultReturnState = HandoffResponsibilityState
