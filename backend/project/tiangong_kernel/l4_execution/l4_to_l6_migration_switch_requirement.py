"""L4 to L6 migration and hot-switch service requirements."""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from ._common import L4_EXECUTION_CLOSURE_SCHEMA_VERSION, ensure_false, ensure_pair_items, ensure_schema_version, ensure_true


@dataclass(frozen=True, slots=True)
class L4ToL6MigrationSwitchRequirement:
    requirement_ref: TypedRef
    migration_service_ref: TypedRef | None = None
    upcast_service_ref: TypedRef | None = None
    checkpoint_service_ref: TypedRef | None = None
    replay_service_ref: TypedRef | None = None
    hot_switch_service_ref: TypedRef | None = None
    requirement_items: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    requirement_only: bool = True
    implements_service: bool = False
    executes_migration: bool = False
    creates_checkpoint: bool = False
    executes_hot_switch: bool = False
    schema_version: str = L4_EXECUTION_CLOSURE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_pair_items(self.requirement_items, "L4ToL6MigrationSwitchRequirement.requirement_items")
        ensure_true(self.requirement_only, "L4ToL6MigrationSwitchRequirement.requirement_only")
        ensure_false(self.implements_service, "L4ToL6MigrationSwitchRequirement.implements_service")
        ensure_false(self.executes_migration, "L4ToL6MigrationSwitchRequirement.executes_migration")
        ensure_false(self.creates_checkpoint, "L4ToL6MigrationSwitchRequirement.creates_checkpoint")
        ensure_false(self.executes_hot_switch, "L4ToL6MigrationSwitchRequirement.executes_hot_switch")
        ensure_schema_version(self.schema_version, "L4ToL6MigrationSwitchRequirement.schema_version")
