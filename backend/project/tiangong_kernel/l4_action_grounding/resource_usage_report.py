"""Resource usage reports for L4 phase 7."""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text, ensure_true


@dataclass(frozen=True, slots=True)
class ResourceUsageReport:
    """Resource usage report; it reads no real system resource counters."""

    resource_usage_report_ref: TypedRef
    action_ref: TypedRef | None = None
    resource_budget_ref: TypedRef | None = None
    token_usage_hint_ref: TypedRef | None = None
    time_usage_hint_ref: TypedRef | None = None
    bytes_usage_hint_ref: TypedRef | None = None
    adapter_call_count_hint_ref: TypedRef | None = None
    external_action_hint_ref: TypedRef | None = None
    process_hint_ref: TypedRef | None = None
    network_hint_ref: TypedRef | None = None
    usage_items: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    report_only: bool = True
    reads_real_system_resource: bool = False
    allocates_real_resource: bool = False
    replaces_l5_budget_decision: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for key, value in self.usage_items:
            ensure_short_text(key, "ResourceUsageReport.usage_items key", 128)
            ensure_short_text(value, "ResourceUsageReport.usage_items value")
        ensure_true(self.report_only, "ResourceUsageReport.report_only")
        ensure_false(self.reads_real_system_resource, "ResourceUsageReport.reads_real_system_resource")
        ensure_false(self.allocates_real_resource, "ResourceUsageReport.allocates_real_resource")
        ensure_false(self.replaces_l5_budget_decision, "ResourceUsageReport.replaces_l5_budget_decision")
        ensure_schema_version(self.schema_version, "ResourceUsageReport.schema_version")
