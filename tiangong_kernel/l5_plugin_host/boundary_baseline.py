"""L5 phase 1 boundary baseline data shell."""

from __future__ import annotations

from dataclasses import dataclass, field

from ._common import L5_PLUGIN_HOST_SCHEMA_VERSION, ensure_ref_items, ensure_ref_text, ensure_schema_version, ensure_short_text


@dataclass(frozen=True, slots=True)
class PluginHostBoundaryBaseline:
    baseline_ref: str
    actor_ref: str
    scope_ref: str
    trace_ref: str
    policy_ref: str
    permit_requirement_ref: str
    lease_requirement_ref: str
    audit_requirement_ref: str
    resource_requirement_ref: str
    approval_ref: str = ""
    handoff_ref: str = ""
    credential_requirement_ref: str = ""
    rollback_requirement_ref: str = ""
    switch_requirement_ref: str = ""
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    provenance_refs: tuple[str, ...] = field(default_factory=tuple)
    accountability_ref: str = ""
    tamper_evidence_ref: str = ""
    summary: str = ""
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name in (
            "baseline_ref",
            "actor_ref",
            "scope_ref",
            "trace_ref",
            "policy_ref",
            "permit_requirement_ref",
            "lease_requirement_ref",
            "audit_requirement_ref",
            "resource_requirement_ref",
        ):
            ensure_ref_text(getattr(self, name), f"PluginHostBoundaryBaseline.{name}")
        for name in (
            "approval_ref",
            "handoff_ref",
            "credential_requirement_ref",
            "rollback_requirement_ref",
            "switch_requirement_ref",
            "accountability_ref",
            "tamper_evidence_ref",
        ):
            ensure_ref_text(getattr(self, name), f"PluginHostBoundaryBaseline.{name}", required=False)
        ensure_ref_items(self.evidence_refs, "PluginHostBoundaryBaseline.evidence_refs")
        ensure_ref_items(self.provenance_refs, "PluginHostBoundaryBaseline.provenance_refs")
        ensure_short_text(self.summary, "PluginHostBoundaryBaseline.summary")
        ensure_schema_version(self.schema_version, "PluginHostBoundaryBaseline.schema_version")
