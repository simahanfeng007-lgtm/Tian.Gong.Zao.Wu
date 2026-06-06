"""L5 phase 1 plugin host context shell."""

from __future__ import annotations

from dataclasses import dataclass, field

from ._common import L5_PLUGIN_HOST_SCHEMA_VERSION, ensure_ref_items, ensure_ref_text, ensure_schema_version, ensure_short_text


@dataclass(frozen=True, slots=True)
class PluginHostContext:
    context_ref: str
    host_ref: str
    actor_ref: str
    scope_ref: str
    trace_ref: str
    policy_ref: str
    approval_ref: str = ""
    handoff_ref: str = ""
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    provenance_refs: tuple[str, ...] = field(default_factory=tuple)
    accountability_ref: str = ""
    tamper_evidence_ref: str = ""
    summary: str = ""
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.context_ref, "PluginHostContext.context_ref")
        ensure_ref_text(self.host_ref, "PluginHostContext.host_ref")
        ensure_ref_text(self.actor_ref, "PluginHostContext.actor_ref")
        ensure_ref_text(self.scope_ref, "PluginHostContext.scope_ref")
        ensure_ref_text(self.trace_ref, "PluginHostContext.trace_ref")
        ensure_ref_text(self.policy_ref, "PluginHostContext.policy_ref")
        ensure_ref_text(self.approval_ref, "PluginHostContext.approval_ref", required=False)
        ensure_ref_text(self.handoff_ref, "PluginHostContext.handoff_ref", required=False)
        ensure_ref_items(self.evidence_refs, "PluginHostContext.evidence_refs")
        ensure_ref_items(self.provenance_refs, "PluginHostContext.provenance_refs")
        ensure_ref_text(self.accountability_ref, "PluginHostContext.accountability_ref", required=False)
        ensure_ref_text(self.tamper_evidence_ref, "PluginHostContext.tamper_evidence_ref", required=False)
        ensure_short_text(self.summary, "PluginHostContext.summary")
        ensure_schema_version(self.schema_version, "PluginHostContext.schema_version")
