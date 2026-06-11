"""Recovery requirement references for future L6 recovery capability."""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text, ensure_true


@dataclass(frozen=True, slots=True)
class RecoveryRequirementRef:
    """Requirement reference only; it implements no recovery system."""

    recovery_requirement_ref: TypedRef
    action_ref: TypedRef
    failure_ref: TypedRef | None = None
    validation_requirement_ref: TypedRef | None = None
    requirement_items: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    ref_only: bool = True
    implements_recovery_system: bool = False
    executes_recovery: bool = False
    executes_rollback: bool = False
    writes_l2_state: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for key, value in self.requirement_items:
            ensure_short_text(key, "RecoveryRequirementRef.requirement_items key", 128)
            ensure_short_text(value, "RecoveryRequirementRef.requirement_items value")
        ensure_true(self.ref_only, "RecoveryRequirementRef.ref_only")
        ensure_false(self.implements_recovery_system, "RecoveryRequirementRef.implements_recovery_system")
        ensure_false(self.executes_recovery, "RecoveryRequirementRef.executes_recovery")
        ensure_false(self.executes_rollback, "RecoveryRequirementRef.executes_rollback")
        ensure_false(self.writes_l2_state, "RecoveryRequirementRef.writes_l2_state")
        ensure_schema_version(self.schema_version, "RecoveryRequirementRef.schema_version")
