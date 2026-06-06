"""Version migration, rollback, and hot-switch refs for L4 handoff."""

from __future__ import annotations

from dataclasses import dataclass

from tiangong_kernel.l0_primitives.identity import TypedRef

from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_true


@dataclass(frozen=True, slots=True)
class L4VersionSwitchRequirement:
    requirement_ref: TypedRef
    adapter_version_compatibility_ref: TypedRef | None = None
    adapter_schema_migration_ref: TypedRef | None = None
    hot_switch_requirement_ref: TypedRef | None = None
    pre_switch_checkpoint_requirement_ref: TypedRef | None = None
    post_switch_observation_requirement_ref: TypedRef | None = None
    switch_rollback_requirement_ref: TypedRef | None = None
    old_event_replay_requirement_ref: TypedRef | None = None
    migration_artifact_ref: TypedRef | None = None
    upcast_preview_ref: TypedRef | None = None
    ref_only: bool = True
    executes_migration: bool = False
    executes_hot_switch: bool = False
    creates_real_checkpoint: bool = False
    executes_rollback: bool = False
    executes_replay: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_true(self.ref_only, "L4VersionSwitchRequirement.ref_only")
        ensure_false(self.executes_migration, "L4VersionSwitchRequirement.executes_migration")
        ensure_false(self.executes_hot_switch, "L4VersionSwitchRequirement.executes_hot_switch")
        ensure_false(self.creates_real_checkpoint, "L4VersionSwitchRequirement.creates_real_checkpoint")
        ensure_false(self.executes_rollback, "L4VersionSwitchRequirement.executes_rollback")
        ensure_false(self.executes_replay, "L4VersionSwitchRequirement.executes_replay")
        ensure_schema_version(self.schema_version, "L4VersionSwitchRequirement.schema_version")


AdapterVersionCompatibilityRequirement = L4VersionSwitchRequirement
AdapterSchemaMigrationRequirement = L4VersionSwitchRequirement
HotSwitchExecutionRequirementRef = TypedRef
PreSwitchCheckpointRequirement = L4VersionSwitchRequirement
PostSwitchObservationRequirement = L4VersionSwitchRequirement
SwitchRollbackExecutionRequirement = L4VersionSwitchRequirement
OldEventReplayRequirement = L4VersionSwitchRequirement
