"""L4 to L6 execution service need for phase 8 closure."""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from ._common import L4_EXECUTION_CLOSURE_SCHEMA_VERSION, L4_L6_SURFACES, ensure_false, ensure_pair_items, ensure_schema_version, ensure_text_items, ensure_true


@dataclass(frozen=True, slots=True)
class L4ToL6ExecutionServiceNeed:
    """Execution service need only; it is not an L6 service implementation."""

    execution_service_need_ref: TypedRef
    service_names: tuple[str, ...] = field(default_factory=lambda: L4_L6_SURFACES)
    need_items: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    need_only: bool = True
    implements_service: bool = False
    executes_external_action: bool = False
    hosts_plugin_or_connector: bool = False
    schema_version: str = L4_EXECUTION_CLOSURE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_text_items(self.service_names, "L4ToL6ExecutionServiceNeed.service_names", 128)
        ensure_pair_items(self.need_items, "L4ToL6ExecutionServiceNeed.need_items")
        ensure_true(self.need_only, "L4ToL6ExecutionServiceNeed.need_only")
        ensure_false(self.implements_service, "L4ToL6ExecutionServiceNeed.implements_service")
        ensure_false(self.executes_external_action, "L4ToL6ExecutionServiceNeed.executes_external_action")
        ensure_false(self.hosts_plugin_or_connector, "L4ToL6ExecutionServiceNeed.hosts_plugin_or_connector")
        ensure_schema_version(self.schema_version, "L4ToL6ExecutionServiceNeed.schema_version")
