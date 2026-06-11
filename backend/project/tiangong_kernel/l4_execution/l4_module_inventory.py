"""L4 module inventory for phase 8 closure."""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from ._common import L4_EXECUTION_CLOSURE_SCHEMA_VERSION, ensure_false, ensure_pair_items, ensure_schema_version, ensure_true


DEFAULT_MODULE_ITEMS = (
    ("phase1_base", "l4_action_grounding", "base execution carriers"),
    ("phase2_boundary", "l4_action_grounding", "permit and boundary references"),
    ("phase3_adapters", "l4_action_grounding", "adapter protocols and disabled real stubs"),
    ("phase4_model_tool", "l4_action_grounding", "model and tool action envelopes"),
    ("phase5_external", "l4_action_grounding", "file network terminal desktop surfaces"),
    ("phase6_return", "l4_action_grounding", "result observation failure and recovery refs"),
    ("phase7_operations", "l4_action_grounding", "transaction resource concurrency replay refs"),
    ("phase8_closure", "l4_execution", "closure inventory handoff and freeze reports"),
)


@dataclass(frozen=True, slots=True)
class L4ModuleInventory:
    """Static L4 module list; it is not a runtime component registry."""

    inventory_ref: TypedRef
    module_items: tuple[tuple[str, str, str], ...] = field(default_factory=lambda: DEFAULT_MODULE_ITEMS)
    inventory_only: bool = True
    creates_runtime_registry: bool = False
    loads_plugins: bool = False
    schedules_components: bool = False
    schema_version: str = L4_EXECUTION_CLOSURE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_pair_items(tuple((phase, module) for phase, module, _ in self.module_items), "L4ModuleInventory.module_items")
        for _, _, summary in self.module_items:
            if len(summary) > 512:
                raise ValueError("L4ModuleInventory.module_items summary must be short")
        ensure_true(self.inventory_only, "L4ModuleInventory.inventory_only")
        ensure_false(self.creates_runtime_registry, "L4ModuleInventory.creates_runtime_registry")
        ensure_false(self.loads_plugins, "L4ModuleInventory.loads_plugins")
        ensure_false(self.schedules_components, "L4ModuleInventory.schedules_components")
        ensure_schema_version(self.schema_version, "L4ModuleInventory.schema_version")
