"""L1 审计证据责任链端口声明。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef
from tiangong_kernel.l0_primitives.trace import TraceContext

from .port_result import PortResult


@dataclass(frozen=True, slots=True)
class AuditChainBoundary:
    """审计链边界，声明事件、证据、责任、来源和完整性要求。"""

    boundary_ref: TypedRef
    event_required: bool = True
    evidence_required: bool = True
    responsibility_required: bool = True
    provenance_required: bool = True
    tamper_required: bool = True
    integrity_required: bool = True
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class AuditChainRequest:
    """审计链请求，承载事件、证据、参与者和责任链引用。"""

    request_ref: TypedRef
    event_ref: TypedRef | None = None
    evidence_ref: TypedRef | None = None
    actor_ref: TypedRef | None = None
    responsibility_chain_ref: TypedRef | None = None
    accountability_ref: TypedRef | None = None
    provenance_ref: TypedRef | None = None
    audit_requirement_ref: TypedRef | None = None
    tamper_evidence_ref: TypedRef | None = None
    integrity_chain_ref: TypedRef | None = None
    schema_version: str = "0.1"


@dataclass(frozen=True, slots=True)
class AuditChainResponse:
    """审计链响应，返回已形成的审计链和缺口引用。"""

    response_ref: TypedRef
    audit_chain_ref: TypedRef
    gap_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"


class AuditChainPort(ABC):
    """审计链端口，只声明边界与提交契约。"""

    @abstractmethod
    def describe_audit_chain_boundary(self, trace: TraceContext) -> PortResult[AuditChainBoundary]:
        raise NotImplementedError

    @abstractmethod
    def submit_audit_chain_request(self, request: AuditChainRequest, trace: TraceContext) -> PortResult[AuditChainResponse]:
        raise NotImplementedError
