"""L5 phase 3 registry audit index declarations.

The audit index holds references only. It never emits real events or writes a
real audit store.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ._common import L5_PLUGIN_HOST_SCHEMA_VERSION, ensure_ref_items, ensure_ref_text, ensure_schema_version, ensure_short_text

_ALLOWED_AUDIT_EVENTS = (
    "registry_record_created",
    "registry_record_updated",
    "registry_record_removed",
    "registry_snapshot_created",
    "registry_delta_created",
    "registry_conflict_detected",
    "registry_quality_gate_passed",
    "registry_quality_gate_failed",
    "registry_forbidden_scan_passed",
    "registry_forbidden_scan_failed",
)


@dataclass(frozen=True, slots=True)
class PluginRegistryAuditEventRef:
    event_ref: str
    event_kind: str
    trace_ref: str
    evidence_ref: str
    responsibility_chain_ref: str
    summary: str
    severity: str = "info"
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.event_ref, "PluginRegistryAuditEventRef.event_ref")
        if self.event_kind not in _ALLOWED_AUDIT_EVENTS:
            raise ValueError("PluginRegistryAuditEventRef.event_kind has unsupported value")
        ensure_ref_text(self.trace_ref, "PluginRegistryAuditEventRef.trace_ref")
        ensure_ref_text(self.evidence_ref, "PluginRegistryAuditEventRef.evidence_ref")
        ensure_ref_text(self.responsibility_chain_ref, "PluginRegistryAuditEventRef.responsibility_chain_ref")
        ensure_short_text(self.summary, "PluginRegistryAuditEventRef.summary")
        ensure_ref_text(self.severity, "PluginRegistryAuditEventRef.severity")
        ensure_schema_version(self.schema_version, "PluginRegistryAuditEventRef.schema_version")


@dataclass(frozen=True, slots=True)
class PluginRegistryAuditIndex:
    audit_index_ref: str
    events: tuple[PluginRegistryAuditEventRef, ...] = field(default_factory=tuple)
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.audit_index_ref, "PluginRegistryAuditIndex.audit_index_ref")
        for event in self.events:
            if not isinstance(event, PluginRegistryAuditEventRef):
                raise ValueError("PluginRegistryAuditIndex.events must contain PluginRegistryAuditEventRef")
        ensure_ref_items(self.evidence_refs, "PluginRegistryAuditIndex.evidence_refs")
        ensure_schema_version(self.schema_version, "PluginRegistryAuditIndex.schema_version")

    def by_event_kind(self, event_kind: str) -> tuple[PluginRegistryAuditEventRef, ...]:
        return tuple(event for event in self.events if event.event_kind == event_kind)
