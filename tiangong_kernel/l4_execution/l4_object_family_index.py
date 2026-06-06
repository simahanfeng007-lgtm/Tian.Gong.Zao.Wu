"""Object family index for L4 phase 8 closure."""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from ._common import L4_EXECUTION_CLOSURE_SCHEMA_VERSION, ensure_false, ensure_pair_items, ensure_schema_version, ensure_true


DEFAULT_FAMILY_ITEMS = (
    ("base_execution", "phase1"),
    ("permit_boundary_refs", "phase2"),
    ("adapter_protocols", "phase3"),
    ("model_tool_actions", "phase4"),
    ("external_action_surfaces", "phase5"),
    ("result_observation_failure_refs", "phase6"),
    ("transaction_resource_concurrency_replay_refs", "phase7"),
    ("closure_handoff_freeze", "phase8"),
)


@dataclass(frozen=True, slots=True)
class L4ObjectFamilyIndex:
    """Static object family index; it does not redefine previous objects."""

    object_family_index_ref: TypedRef
    family_items: tuple[tuple[str, str], ...] = field(default_factory=lambda: DEFAULT_FAMILY_ITEMS)
    index_only: bool = True
    duplicates_existing_objects: bool = False
    mutates_previous_phase_interfaces: bool = False
    schema_version: str = L4_EXECUTION_CLOSURE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_pair_items(self.family_items, "L4ObjectFamilyIndex.family_items")
        ensure_true(self.index_only, "L4ObjectFamilyIndex.index_only")
        ensure_false(self.duplicates_existing_objects, "L4ObjectFamilyIndex.duplicates_existing_objects")
        ensure_false(self.mutates_previous_phase_interfaces, "L4ObjectFamilyIndex.mutates_previous_phase_interfaces")
        ensure_schema_version(self.schema_version, "L4ObjectFamilyIndex.schema_version")
