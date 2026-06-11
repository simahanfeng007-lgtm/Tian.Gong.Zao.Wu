"""L4 to L5 version switch boundary requirement."""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from ._common import L4_EXECUTION_CLOSURE_SCHEMA_VERSION, ensure_false, ensure_pair_items, ensure_schema_version, ensure_true


@dataclass(frozen=True, slots=True)
class L4ToL5VersionSwitchRequirement:
    requirement_ref: TypedRef
    version_slot_ref: TypedRef | None = None
    hot_switch_permit_ref: TypedRef | None = None
    rollback_permission_ref: TypedRef | None = None
    replay_permission_ref: TypedRef | None = None
    breaking_change_gate_ref: TypedRef | None = None
    requirement_items: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    requirement_only: bool = True
    activates_version_slot: bool = False
    grants_switch_permission: bool = False
    executes_rollback: bool = False
    executes_replay: bool = False
    schema_version: str = L4_EXECUTION_CLOSURE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_pair_items(self.requirement_items, "L4ToL5VersionSwitchRequirement.requirement_items")
        ensure_true(self.requirement_only, "L4ToL5VersionSwitchRequirement.requirement_only")
        ensure_false(self.activates_version_slot, "L4ToL5VersionSwitchRequirement.activates_version_slot")
        ensure_false(self.grants_switch_permission, "L4ToL5VersionSwitchRequirement.grants_switch_permission")
        ensure_false(self.executes_rollback, "L4ToL5VersionSwitchRequirement.executes_rollback")
        ensure_false(self.executes_replay, "L4ToL5VersionSwitchRequirement.executes_replay")
        ensure_schema_version(self.schema_version, "L4ToL5VersionSwitchRequirement.schema_version")
