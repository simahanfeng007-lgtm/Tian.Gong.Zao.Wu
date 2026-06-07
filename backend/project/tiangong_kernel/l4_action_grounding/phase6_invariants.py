"""Phase 6 invariants for returns, observations, audit refs, and recovery advice."""

from __future__ import annotations

from dataclasses import dataclass

from tiangong_kernel.l0_primitives.identity import TypedRef

from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text, ensure_true


@dataclass(frozen=True, slots=True)
class Phase6Invariant:
    invariant_ref: TypedRef
    invariant_name: str
    ref_only: bool = True
    l4_can_override: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_short_text(self.invariant_name, "Phase6Invariant.invariant_name", 128)
        ensure_true(self.ref_only, "Phase6Invariant.ref_only")
        ensure_false(self.l4_can_override, "Phase6Invariant.l4_can_override")
        ensure_schema_version(self.schema_version, "Phase6Invariant.schema_version")


@dataclass(frozen=True, slots=True)
class NoAuditWriteInL4Invariant(Phase6Invariant):
    invariant_name: str = "NoAuditWriteInL4Invariant"


@dataclass(frozen=True, slots=True)
class NoPermitIssuanceInL4Invariant(Phase6Invariant):
    invariant_name: str = "NoPermitIssuanceInL4Invariant"


@dataclass(frozen=True, slots=True)
class NoRealObservationInL4Invariant(Phase6Invariant):
    invariant_name: str = "NoRealObservationInL4Invariant"


@dataclass(frozen=True, slots=True)
class NoRetryRecoveryRollbackInL4Invariant(Phase6Invariant):
    invariant_name: str = "NoRetryRecoveryRollbackInL4Invariant"


@dataclass(frozen=True, slots=True)
class NoL2StateWriteFromReturnInvariant(Phase6Invariant):
    invariant_name: str = "NoL2StateWriteFromReturnInvariant"
