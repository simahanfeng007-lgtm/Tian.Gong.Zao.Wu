"""L2 审计证据责任链状态对象。"""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from .base_state import L2_STATE_SCHEMA_VERSION, L2StateMetadata
from .state_identity import L2StateIdentity
from .state_status import L2StateStatus


@dataclass(frozen=True, slots=True)
class AuditChainState:
    """审计链状态，绑定事件、证据、责任链、来源和完整性引用。"""

    identity: L2StateIdentity
    status: L2StateStatus
    event_ref: TypedRef | None = None
    evidence_ref: TypedRef | None = None
    responsibility_chain_ref: TypedRef | None = None
    provenance_ref: TypedRef | None = None
    tamper_evidence_ref: TypedRef | None = None
    integrity_chain_ref: TypedRef | None = None
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION


@dataclass(frozen=True, slots=True)
class AuditCoverageState:
    """审计覆盖状态，记录已覆盖引用和缺失引用。"""

    identity: L2StateIdentity
    status: L2StateStatus
    covered_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    missing_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION


@dataclass(frozen=True, slots=True)
class AuditGapState:
    """审计缺口状态，标记事件、证据、责任、来源或完整性缺失。"""

    identity: L2StateIdentity
    status: L2StateStatus
    gap_ref: TypedRef
    missing_event: bool = False
    missing_evidence: bool = False
    missing_responsibility: bool = False
    missing_provenance: bool = False
    missing_integrity: bool = False
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION
