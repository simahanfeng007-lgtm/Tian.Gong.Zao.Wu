"""L3 event-first audit chain projection advice."""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from .orchestration_identity import L3_ORCHESTRATION_SCHEMA_VERSION


@dataclass(frozen=True, slots=True)
class AuditChainProjection:
    projection_ref: TypedRef
    event_ref: TypedRef | None = None
    evidence_ref: TypedRef | None = None
    responsibility_chain_ref: TypedRef | None = None
    provenance_ref: TypedRef | None = None
    audit_gap_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    advisory_only: bool = True
    writes_audit: bool = False
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION
