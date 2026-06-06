"""Phase 7 invariants for transaction/resource/concurrency/replay boundaries."""

from __future__ import annotations

from dataclasses import dataclass

from tiangong_kernel.l0_primitives.identity import TypedRef

from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text, ensure_true


@dataclass(frozen=True, slots=True)
class Phase7Invariant:
    invariant_ref: TypedRef
    invariant_name: str
    ref_only: bool = True
    l4_can_override: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_short_text(self.invariant_name, "Phase7Invariant.invariant_name", 128)
        ensure_true(self.ref_only, "Phase7Invariant.ref_only")
        ensure_false(self.l4_can_override, "Phase7Invariant.l4_can_override")
        ensure_schema_version(self.schema_version, "Phase7Invariant.schema_version")


@dataclass(frozen=True, slots=True)
class TransactionRefIsNotCommitInvariant(Phase7Invariant):
    invariant_name: str = "TransactionRefIsNotCommitInvariant"


@dataclass(frozen=True, slots=True)
class RollbackIntentIsNotRollbackInvariant(Phase7Invariant):
    invariant_name: str = "RollbackIntentIsNotRollbackInvariant"


@dataclass(frozen=True, slots=True)
class ResourceBudgetRefIsNotAllocationInvariant(Phase7Invariant):
    invariant_name: str = "ResourceBudgetRefIsNotAllocationInvariant"


@dataclass(frozen=True, slots=True)
class ConcurrencyScopeIsNotSchedulerInvariant(Phase7Invariant):
    invariant_name: str = "ConcurrencyScopeIsNotSchedulerInvariant"


@dataclass(frozen=True, slots=True)
class LockRefIsNotRealLockInvariant(Phase7Invariant):
    invariant_name: str = "LockRefIsNotRealLockInvariant"


@dataclass(frozen=True, slots=True)
class ReplaySummaryContainsNoPlainCredentialInvariant(Phase7Invariant):
    invariant_name: str = "ReplaySummaryContainsNoPlainCredentialInvariant"


@dataclass(frozen=True, slots=True)
class NoResourceBudgetAllocationInL4Invariant(Phase7Invariant):
    invariant_name: str = "NoResourceBudgetAllocationInL4Invariant"


@dataclass(frozen=True, slots=True)
class NoConcurrencyAuthorizationInL4Invariant(Phase7Invariant):
    invariant_name: str = "NoConcurrencyAuthorizationInL4Invariant"


@dataclass(frozen=True, slots=True)
class NoCommitOrRollbackAuthorizationInL4Invariant(Phase7Invariant):
    invariant_name: str = "NoCommitOrRollbackAuthorizationInL4Invariant"
