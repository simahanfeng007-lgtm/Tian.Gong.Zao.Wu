"""L4 to L6 recovery requirement for phase 8 closure."""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from ._common import L4_EXECUTION_CLOSURE_SCHEMA_VERSION, ensure_false, ensure_pair_items, ensure_schema_version, ensure_true


@dataclass(frozen=True, slots=True)
class L4ToL6RecoveryRequirement:
    """Recovery requirement only; it executes no recovery."""

    recovery_requirement_ref: TypedRef
    failure_ref: TypedRef | None = None
    rollback_intent_ref: TypedRef | None = None
    recovery_items: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    requirement_only: bool = True
    executes_recovery: bool = False
    executes_rollback: bool = False
    restores_external_state: bool = False
    schema_version: str = L4_EXECUTION_CLOSURE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_pair_items(self.recovery_items, "L4ToL6RecoveryRequirement.recovery_items")
        ensure_true(self.requirement_only, "L4ToL6RecoveryRequirement.requirement_only")
        ensure_false(self.executes_recovery, "L4ToL6RecoveryRequirement.executes_recovery")
        ensure_false(self.executes_rollback, "L4ToL6RecoveryRequirement.executes_rollback")
        ensure_false(self.restores_external_state, "L4ToL6RecoveryRequirement.restores_external_state")
        ensure_schema_version(self.schema_version, "L4ToL6RecoveryRequirement.schema_version")
