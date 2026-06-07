"""Declaration-only audit index for L5 phase 4 lifecycle and mount checks."""

from __future__ import annotations

from dataclasses import dataclass, field

from ._common import L5_PLUGIN_HOST_SCHEMA_VERSION, ensure_ref_items, ensure_ref_text, ensure_schema_version, ensure_short_text
from .lifecycle_declaration import lifecycle_declaration_digest


@dataclass(frozen=True, slots=True)
class PluginLifecycleAuditEventRef:
    event_ref: str
    event_kind_ref: str
    trace_ref: str
    evidence_ref: str
    responsibility_chain_ref: str
    severity: str = "info"
    summary: str = ""
    actor_ref: str = ""
    scope_ref: str = ""
    policy_ref: str = ""
    approval_ref: str = ""
    accountability_ref: str = ""
    provenance_refs: tuple[str, ...] = field(default_factory=tuple)
    tamper_evidence_ref: str = ""
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name in ("event_ref", "event_kind_ref", "trace_ref", "evidence_ref", "responsibility_chain_ref"):
            ensure_ref_text(getattr(self, name), f"PluginLifecycleAuditEventRef.{name}")
        for name in ("actor_ref", "scope_ref", "policy_ref", "approval_ref", "accountability_ref", "tamper_evidence_ref"):
            ensure_ref_text(getattr(self, name), f"PluginLifecycleAuditEventRef.{name}", required=False)
        ensure_ref_items(self.provenance_refs, "PluginLifecycleAuditEventRef.provenance_refs")
        ensure_short_text(self.severity, "PluginLifecycleAuditEventRef.severity", 16)
        ensure_short_text(self.summary, "PluginLifecycleAuditEventRef.summary")
        ensure_schema_version(self.schema_version, "PluginLifecycleAuditEventRef.schema_version")


@dataclass(frozen=True, slots=True)
class PluginLifecycleAuditIndex:
    audit_index_ref: str
    audit_events: tuple[PluginLifecycleAuditEventRef, ...] = field(default_factory=tuple)
    event_kind_refs: tuple[str, ...] = field(default_factory=tuple)
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    trace_ref: str = ""
    policy_ref: str = ""
    responsibility_chain_ref: str = ""
    actor_ref: str = ""
    scope_ref: str = ""
    approval_ref: str = ""
    accountability_ref: str = ""
    provenance_refs: tuple[str, ...] = field(default_factory=tuple)
    tamper_evidence_ref: str = ""
    audit_index_digest: str = ""
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.audit_index_ref, "PluginLifecycleAuditIndex.audit_index_ref")
        for item in self.audit_events:
            if not isinstance(item, PluginLifecycleAuditEventRef):
                raise ValueError("PluginLifecycleAuditIndex.audit_events must contain PluginLifecycleAuditEventRef")
        for name in ("event_kind_refs", "evidence_refs", "provenance_refs"):
            ensure_ref_items(getattr(self, name), f"PluginLifecycleAuditIndex.{name}")
        for name in ("trace_ref", "policy_ref", "responsibility_chain_ref", "actor_ref", "scope_ref", "approval_ref", "accountability_ref", "tamper_evidence_ref"):
            ensure_ref_text(getattr(self, name), f"PluginLifecycleAuditIndex.{name}", required=False)
        ensure_schema_version(self.schema_version, "PluginLifecycleAuditIndex.schema_version")
        if not self.audit_index_digest:
            object.__setattr__(self, "audit_index_digest", lifecycle_declaration_digest(self))


@dataclass(frozen=True, slots=True)
class PluginLifecycleAuditIndexBuilder:
    builder_ref: str
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.builder_ref, "PluginLifecycleAuditIndexBuilder.builder_ref")
        ensure_schema_version(self.schema_version, "PluginLifecycleAuditIndexBuilder.schema_version")

    def build_index(self, event_refs: tuple[PluginLifecycleAuditEventRef, ...]) -> PluginLifecycleAuditIndex:
        return PluginLifecycleAuditIndex(
            audit_index_ref="lifecycle_audit_index:l5_phase4",
            audit_events=event_refs,
            event_kind_refs=tuple(item.event_kind_ref for item in event_refs),
            evidence_refs=tuple(item.evidence_ref for item in event_refs),
            trace_ref=event_refs[0].trace_ref if event_refs else "trace:l5_phase4_audit_index",
            responsibility_chain_ref=event_refs[0].responsibility_chain_ref if event_refs else "responsibility:l5_phase4_audit_index",
            actor_ref=event_refs[0].actor_ref if event_refs else "actor:l5_phase4",
            scope_ref=event_refs[0].scope_ref if event_refs else "scope:l5_phase4",
            provenance_refs=tuple(ref for item in event_refs for ref in item.provenance_refs),
            tamper_evidence_ref=event_refs[0].tamper_evidence_ref if event_refs else "tamper:l5_phase4_audit_index",
        )


__all__ = (
    "PluginLifecycleAuditEventRef",
    "PluginLifecycleAuditIndex",
    "PluginLifecycleAuditIndexBuilder",
)
