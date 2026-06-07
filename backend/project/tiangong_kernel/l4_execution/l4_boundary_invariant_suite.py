"""Boundary invariant suite for L4 phase 8 closure."""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from ._common import L4_EXECUTION_CLOSURE_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_text_items, ensure_true


DEFAULT_INVARIANT_NAMES = (
    "NoLiveExecutionWithoutL5Invariant",
    "NoL4PermissionDecisionInvariant",
    "NoL4AuditWriterInvariant",
    "NoRetryRecoveryRollbackInL4Invariant",
    "NoL2StateWriteFromReturnInvariant",
    "TransactionRefIsNotCommitInvariant",
    "NoResourceBudgetAllocationInL4Invariant",
    "NoConcurrencyAuthorizationInL4Invariant",
    "NoCommitOrRollbackAuthorizationInL4Invariant",
)


@dataclass(frozen=True, slots=True)
class L4BoundaryInvariantSuite:
    """Static suite of key L4 invariants; it grants no permission."""

    invariant_suite_ref: TypedRef
    invariant_names: tuple[str, ...] = field(default_factory=lambda: DEFAULT_INVARIANT_NAMES)
    suite_only: bool = True
    grants_permission: bool = False
    signs_permit: bool = False
    writes_l2_state: bool = False
    implements_l6_subsystem: bool = False
    schema_version: str = L4_EXECUTION_CLOSURE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_text_items(self.invariant_names, "L4BoundaryInvariantSuite.invariant_names", 128)
        ensure_true(self.suite_only, "L4BoundaryInvariantSuite.suite_only")
        ensure_false(self.grants_permission, "L4BoundaryInvariantSuite.grants_permission")
        ensure_false(self.signs_permit, "L4BoundaryInvariantSuite.signs_permit")
        ensure_false(self.writes_l2_state, "L4BoundaryInvariantSuite.writes_l2_state")
        ensure_false(self.implements_l6_subsystem, "L4BoundaryInvariantSuite.implements_l6_subsystem")
        ensure_schema_version(self.schema_version, "L4BoundaryInvariantSuite.schema_version")
