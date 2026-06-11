"""Declarative audit evidence and responsibility-chain requirements."""

from __future__ import annotations

from dataclasses import dataclass, field

from ._common import L5_PLUGIN_HOST_SCHEMA_VERSION, ensure_bool, ensure_ref_items, ensure_ref_text, ensure_schema_version, ensure_text_items


@dataclass(frozen=True, slots=True)
class PluginAuditDeclaration:
    audit_event_kinds: tuple[str, ...] = field(default_factory=tuple)
    evidence_required: bool = True
    trace_required: bool = True
    replay_policy_ref: str = ""
    responsibility_chain_ref: str = ""
    actor_required: bool = True
    scope_required: bool = True
    accountability_required: bool = True
    tamper_evidence_required: bool = True
    provenance_policy_ref: str = ""
    evidence_boundary_ref: str = ""
    audit_retention_policy_ref: str = ""
    audit_store_written: bool = False
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_text_items(self.audit_event_kinds, "PluginAuditDeclaration.audit_event_kinds", limit=128)
        for name in (
            "evidence_required",
            "trace_required",
            "actor_required",
            "scope_required",
            "accountability_required",
            "tamper_evidence_required",
            "audit_store_written",
        ):
            ensure_bool(getattr(self, name), f"PluginAuditDeclaration.{name}")
        if self.audit_store_written:
            raise ValueError("PluginAuditDeclaration must not write audit stores")
        for name in (
            "replay_policy_ref",
            "responsibility_chain_ref",
            "provenance_policy_ref",
            "evidence_boundary_ref",
            "audit_retention_policy_ref",
        ):
            ensure_ref_text(getattr(self, name), f"PluginAuditDeclaration.{name}", required=False)
        ensure_schema_version(self.schema_version, "PluginAuditDeclaration.schema_version")
