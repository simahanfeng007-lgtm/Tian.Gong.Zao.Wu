"""Public export map for L4 phase 8 closure."""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from ._common import L4_EXECUTION_CLOSURE_SCHEMA_VERSION, ensure_false, ensure_pair_items, ensure_schema_version, ensure_true


DEFAULT_EXPORT_ITEMS = (
    ("ActionGroundingContext", "phase1_base"),
    ("ExecutionPermitRef", "phase2_boundary"),
    ("AdapterDescriptor", "phase3_adapters"),
    ("ModelActionRequest", "phase4_model_tool"),
    ("FileActionRequest", "phase5_external"),
    ("ActionOutcomeEnvelope", "phase6_return"),
    ("ExecutionTransactionRef", "phase7_operations"),
    ("L4ModuleInventory", "phase8_closure"),
    ("L4ToL5HandoffEnvelope", "phase8_handoff"),
    ("L4ToL6AdapterRequirement", "phase8_handoff"),
)


@dataclass(frozen=True, slots=True)
class L4PublicExportMap:
    """Static public export map; it exposes no live adapter execution entry."""

    export_map_ref: TypedRef
    export_items: tuple[tuple[str, str], ...] = field(default_factory=lambda: DEFAULT_EXPORT_ITEMS)
    map_only: bool = True
    exposes_real_adapter_execution: bool = False
    exposes_permission_decision: bool = False
    exposes_l6_service: bool = False
    schema_version: str = L4_EXECUTION_CLOSURE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_pair_items(self.export_items, "L4PublicExportMap.export_items")
        ensure_true(self.map_only, "L4PublicExportMap.map_only")
        ensure_false(self.exposes_real_adapter_execution, "L4PublicExportMap.exposes_real_adapter_execution")
        ensure_false(self.exposes_permission_decision, "L4PublicExportMap.exposes_permission_decision")
        ensure_false(self.exposes_l6_service, "L4PublicExportMap.exposes_l6_service")
        ensure_schema_version(self.schema_version, "L4PublicExportMap.schema_version")
