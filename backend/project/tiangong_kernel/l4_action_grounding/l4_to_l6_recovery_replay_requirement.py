"""L4 to L6 recovery/replay requirement references for phase 7."""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text, ensure_true


@dataclass(frozen=True, slots=True)
class L4ToL6RecoveryReplayRequirement:
    """Requirement reference only; it implements no recovery or replay service."""

    requirement_ref: TypedRef
    recovery_requirement_ref: TypedRef | None = None
    replay_requirement_ref: TypedRef | None = None
    reconciliation_requirement_ref: TypedRef | None = None
    requirement_items: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    ref_only: bool = True
    implements_recovery_system: bool = False
    implements_replay_system: bool = False
    executes_replay: bool = False
    executes_rollback: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for key, value in self.requirement_items:
            ensure_short_text(key, "L4ToL6RecoveryReplayRequirement.requirement_items key", 128)
            ensure_short_text(value, "L4ToL6RecoveryReplayRequirement.requirement_items value")
        ensure_true(self.ref_only, "L4ToL6RecoveryReplayRequirement.ref_only")
        ensure_false(self.implements_recovery_system, "L4ToL6RecoveryReplayRequirement.implements_recovery_system")
        ensure_false(self.implements_replay_system, "L4ToL6RecoveryReplayRequirement.implements_replay_system")
        ensure_false(self.executes_replay, "L4ToL6RecoveryReplayRequirement.executes_replay")
        ensure_false(self.executes_rollback, "L4ToL6RecoveryReplayRequirement.executes_rollback")
        ensure_schema_version(self.schema_version, "L4ToL6RecoveryReplayRequirement.schema_version")
