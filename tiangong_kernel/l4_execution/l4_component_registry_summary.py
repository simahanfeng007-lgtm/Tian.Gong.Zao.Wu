"""Component registry summary for L4 phase 8 closure."""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from ._common import L4_EXECUTION_CLOSURE_SCHEMA_VERSION, ensure_false, ensure_pair_items, ensure_schema_version, ensure_true


@dataclass(frozen=True, slots=True)
class L4ComponentRegistrySummary:
    """Component summary only; not a dynamic runtime registry."""

    component_registry_summary_ref: TypedRef
    component_items: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    summary_only: bool = True
    creates_runtime_registry: bool = False
    dynamically_loads_plugins: bool = False
    hosts_l6_subsystem: bool = False
    schema_version: str = L4_EXECUTION_CLOSURE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_pair_items(self.component_items, "L4ComponentRegistrySummary.component_items")
        ensure_true(self.summary_only, "L4ComponentRegistrySummary.summary_only")
        ensure_false(self.creates_runtime_registry, "L4ComponentRegistrySummary.creates_runtime_registry")
        ensure_false(self.dynamically_loads_plugins, "L4ComponentRegistrySummary.dynamically_loads_plugins")
        ensure_false(self.hosts_l6_subsystem, "L4ComponentRegistrySummary.hosts_l6_subsystem")
        ensure_schema_version(self.schema_version, "L4ComponentRegistrySummary.schema_version")
