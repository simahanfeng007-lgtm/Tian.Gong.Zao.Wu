"""L6 invocation and output envelopes.

Invocation envelopes carry read-only refs after upstream orchestration and host
governance. Output envelopes carry suggestions, candidates, projections, events,
and handoff refs only; they never perform external side effects.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ._common import L6_COMMON_SCHEMA_VERSION, ensure_ref_items, ensure_ref_or_summary_items, ensure_ref_text, ensure_schema_version


@dataclass(frozen=True, slots=True)
class L6PluginInvocationEnvelope:
    invocation_ref: str = "l6:invocation_ref"
    plugin_id: str = "l6.plugin.placeholder"
    orchestration_ref: str = "l3:orchestration_ref"
    l5_governance_binding_ref: str = "l5:governance_binding_ref"
    read_only_context_projection_refs: tuple[str, ...] = field(default_factory=lambda: ("context:l6_read_only_context_projection",))
    state_projection_refs: tuple[str, ...] = field(default_factory=lambda: ("projection:l6_state_projection_ref",))
    model_capability_dispatch_refs: tuple[str, ...] = field(default_factory=tuple)
    tool_capability_dispatch_refs: tuple[str, ...] = field(default_factory=tuple)
    permission_scope_refs: tuple[str, ...] = field(default_factory=lambda: ("permission:l6_permission_scope_ref",))
    budget_scope_refs: tuple[str, ...] = field(default_factory=lambda: ("budget:l6_budget_scope_ref",))
    audit_envelope_ref: str = "audit:l6_invocation_audit_envelope_ref"
    credential_policy_refs: tuple[str, ...] = field(default_factory=tuple)
    event_digest_refs: tuple[str, ...] = field(default_factory=tuple)
    handoff_digest_refs: tuple[str, ...] = field(default_factory=tuple)
    contains_raw_credential: bool = False
    contains_tool_handle: bool = False
    contains_model_client: bool = False
    contains_state_writer: bool = False
    contains_callable: bool = False
    read_only: bool = True
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.invocation_ref, "L6PluginInvocationEnvelope.invocation_ref")
        ensure_ref_text(self.plugin_id, "L6PluginInvocationEnvelope.plugin_id")
        ensure_ref_text(self.orchestration_ref, "L6PluginInvocationEnvelope.orchestration_ref")
        ensure_ref_text(self.l5_governance_binding_ref, "L6PluginInvocationEnvelope.l5_governance_binding_ref")
        for field_name in (
            "read_only_context_projection_refs", "state_projection_refs", "model_capability_dispatch_refs",
            "tool_capability_dispatch_refs", "permission_scope_refs", "budget_scope_refs", "credential_policy_refs",
            "event_digest_refs", "handoff_digest_refs",
        ):
            ensure_ref_items(getattr(self, field_name), f"L6PluginInvocationEnvelope.{field_name}")
        ensure_ref_text(self.audit_envelope_ref, "L6PluginInvocationEnvelope.audit_envelope_ref")
        if any((self.contains_raw_credential, self.contains_tool_handle, self.contains_model_client, self.contains_state_writer, self.contains_callable)):
            raise ValueError("L6 invocation envelope cannot contain live credential, tool, model, writer, or callable objects")
        if not self.read_only:
            raise ValueError("L6 invocation envelope must remain read-only")
        ensure_schema_version(self.schema_version)


@dataclass(frozen=True, slots=True)
class L6PluginOutputEnvelope:
    output_ref: str = "l6:output_ref"
    plugin_id: str = "l6.plugin.placeholder"
    suggestion_refs: tuple[str, ...] = field(default_factory=tuple)
    candidate_refs: tuple[str, ...] = field(default_factory=tuple)
    summary_items: tuple[str, ...] = field(default_factory=tuple)
    projection_refs: tuple[str, ...] = field(default_factory=tuple)
    event_publication_refs: tuple[str, ...] = field(default_factory=tuple)
    handoff_refs: tuple[str, ...] = field(default_factory=tuple)
    audit_summary_refs: tuple[str, ...] = field(default_factory=lambda: ("audit:l6_output_audit_summary_ref",))
    quality_gate_refs: tuple[str, ...] = field(default_factory=tuple)
    failure_refs: tuple[str, ...] = field(default_factory=tuple)
    degradation_refs: tuple[str, ...] = field(default_factory=tuple)
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    side_effect_free: bool = True
    writes_state: bool = False
    writes_audit_record: bool = False
    calls_model: bool = False
    invokes_tool: bool = False
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.output_ref, "L6PluginOutputEnvelope.output_ref")
        ensure_ref_text(self.plugin_id, "L6PluginOutputEnvelope.plugin_id")
        for field_name in (
            "suggestion_refs", "candidate_refs", "projection_refs", "event_publication_refs", "handoff_refs",
            "audit_summary_refs", "quality_gate_refs", "failure_refs", "degradation_refs", "evidence_refs",
        ):
            ensure_ref_items(getattr(self, field_name), f"L6PluginOutputEnvelope.{field_name}")
        ensure_ref_or_summary_items(self.summary_items, "L6PluginOutputEnvelope.summary_items")
        if not self.side_effect_free or self.writes_state or self.writes_audit_record or self.calls_model or self.invokes_tool:
            raise ValueError("L6 output envelope can only carry refs, summaries, candidates, projections, and handoff declarations")
        ensure_schema_version(self.schema_version)
