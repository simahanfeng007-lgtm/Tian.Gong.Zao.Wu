"""L4 to L6 adapter requirement for phase 8 closure."""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from ._common import L4_EXECUTION_CLOSURE_SCHEMA_VERSION, L4_L6_SURFACES, ensure_false, ensure_pair_items, ensure_schema_version, ensure_text_items, ensure_true


@dataclass(frozen=True, slots=True)
class L4ToL6AdapterRequirement:
    """Adapter requirement only; it implements no adapter."""

    adapter_requirement_ref: TypedRef
    adapter_descriptor_ref: TypedRef | None = None
    capability_descriptor_ref: TypedRef | None = None
    risk_surface_ref: TypedRef | None = None
    sandbox_requirement_ref: TypedRef | None = None
    quality_gate_requirement_ref: TypedRef | None = None
    migration_switch_requirement_ref: TypedRef | None = None
    data_access_manifest_requirement_ref: TypedRef | None = None
    external_disclosure_manifest_requirement_ref: TypedRef | None = None
    required_adapters: tuple[str, ...] = field(default_factory=lambda: L4_L6_SURFACES[:10])
    priority_items: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    requirement_only: bool = True
    implements_adapter: bool = False
    calls_model: bool = False
    invokes_tool: bool = False
    schema_version: str = L4_EXECUTION_CLOSURE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_text_items(self.required_adapters, "L4ToL6AdapterRequirement.required_adapters", 128)
        ensure_pair_items(self.priority_items, "L4ToL6AdapterRequirement.priority_items")
        ensure_true(self.requirement_only, "L4ToL6AdapterRequirement.requirement_only")
        ensure_false(self.implements_adapter, "L4ToL6AdapterRequirement.implements_adapter")
        ensure_false(self.calls_model, "L4ToL6AdapterRequirement.calls_model")
        ensure_false(self.invokes_tool, "L4ToL6AdapterRequirement.invokes_tool")
        ensure_schema_version(self.schema_version, "L4ToL6AdapterRequirement.schema_version")
