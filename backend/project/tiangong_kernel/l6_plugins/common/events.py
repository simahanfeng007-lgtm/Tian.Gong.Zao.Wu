"""L6 phase2 versioned plugin event envelopes.

Events are governance signals. They never call plugins, tools, models, lower
layer adapters, files, networks, databases, or state writers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from ._common import (
    L6_COMMON_SCHEMA_VERSION,
    ensure_bool,
    ensure_digest,
    ensure_no_live_or_sensitive_text,
    ensure_ref_items,
    ensure_ref_text,
    ensure_schema_version,
    stable_digest,
)
from .audit import L6AuditTraceEnvelope


class L6PluginEventKind(str, Enum):
    LIFECYCLE = "lifecycle"
    INVOCATION = "invocation"
    HANDOFF = "handoff"
    PROJECTION = "projection"
    ADMISSION = "admission"
    QUALITY_GATE = "quality_gate"
    VERSION_GOVERNANCE = "version_governance"
    CONTEXT_BELIEF_WORLD = "context_belief_world"


@dataclass(frozen=True, slots=True)
class VersionedPluginEventEnvelope:
    event_ref: str = "event:l6_phase2_event"
    event_kind: L6PluginEventKind | str = L6PluginEventKind.LIFECYCLE
    event_schema_version: str = L6_COMMON_SCHEMA_VERSION
    event_contract_version: str = "ref:l6_phase2_event_contract_version"
    producer_plugin_ref: str = "l6:producer_plugin"
    producer_plugin_version_ref: str = "ref:l6_producer_plugin_version"
    producer_lifecycle_ref: str = "lifecycle:l6_producer_lifecycle"
    consumer_plugin_refs: tuple[str, ...] = field(default_factory=tuple)
    consumer_contract_range_ref: str = "ref:l6_consumer_contract_range"
    event_scope_ref: str = "ref:l6_event_scope"
    target_scope_ref: str = "ref:l6_event_target_scope"
    payload_summary_ref: str = "summary:l6_event_payload_summary"
    payload_digest: str = "" 
    event_privacy_class: str = "summary:minimal_disclosure"
    causality_refs: tuple[str, ...] = field(default_factory=lambda: ("event:l6_causality_root",))
    correlation_ref: str = "ref:l6_event_correlation"
    parent_event_ref: str = "event:l6_parent_event"
    idempotency_key_ref: str = "ref:l6_event_idempotency"
    dedupe_key_ref: str = "ref:l6_event_dedupe"
    sequence_ref: str = "ref:l6_event_sequence"
    ordering_ref: str = "ref:l6_event_ordering"
    ttl_ref: str = "ref:l6_event_ttl"
    replay_policy_ref: str = "policy:l6_event_replay_policy"
    replay_compatibility_ref: str = "ref:l6_event_replay_compatibility"
    upcast_policy_ref: str = "policy:l6_event_upcast_policy"
    deprecation_policy_ref: str = "policy:l6_event_deprecation_policy"
    breaking_change_assessment_ref: str = "ref:l6_event_breaking_change_assessment"
    policy_refs: tuple[str, ...] = field(default_factory=lambda: ("policy:l6_event_not_execution",))
    budget_refs: tuple[str, ...] = field(default_factory=lambda: ("budget:l6_event_budget_ref",))
    audit_requirement_ref: str = "audit:l6_event_audit_requirement"
    evidence_refs: tuple[str, ...] = field(default_factory=lambda: ("evidence:l6_event_evidence",))
    provenance_refs: tuple[str, ...] = field(default_factory=lambda: ("evidence:l6_event_provenance",))
    trace_ref: str = "ref:l6_event_trace"
    responsibility_chain_ref: str = "responsibility:l6_event_chain"
    accountability_ref: str = "responsibility:l6_event_accountability"
    tamper_evidence_ref: str = "evidence:l6_event_tamper"
    redaction_state: str = "summary:redacted"
    public_projection_ref: str = "public:l6_event_projection"
    audit_trace_envelope: L6AuditTraceEnvelope = field(default_factory=L6AuditTraceEnvelope)
    calls_model: bool = False
    invokes_tool: bool = False
    writes_state: bool = False
    direct_plugin_call: bool = False
    carries_raw_payload: bool = False
    action_replay_allowed: bool = False
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.event_ref, "VersionedPluginEventEnvelope.event_ref")
        object.__setattr__(self, "event_kind", L6PluginEventKind(self.event_kind))
        ensure_schema_version(self.event_schema_version, "event_schema_version")
        for field_name in (
            "event_contract_version",
            "producer_plugin_ref",
            "producer_plugin_version_ref",
            "producer_lifecycle_ref",
            "consumer_contract_range_ref",
            "event_scope_ref",
            "target_scope_ref",
            "payload_summary_ref",
            "correlation_ref",
            "parent_event_ref",
            "idempotency_key_ref",
            "dedupe_key_ref",
            "sequence_ref",
            "ordering_ref",
            "ttl_ref",
            "replay_policy_ref",
            "replay_compatibility_ref",
            "upcast_policy_ref",
            "deprecation_policy_ref",
            "breaking_change_assessment_ref",
            "audit_requirement_ref",
            "trace_ref",
            "responsibility_chain_ref",
            "accountability_ref",
            "tamper_evidence_ref",
            "public_projection_ref",
        ):
            ensure_ref_text(getattr(self, field_name), f"VersionedPluginEventEnvelope.{field_name}")
        ensure_no_live_or_sensitive_text(self.event_privacy_class, "VersionedPluginEventEnvelope.event_privacy_class")
        ensure_no_live_or_sensitive_text(self.redaction_state, "VersionedPluginEventEnvelope.redaction_state")
        ensure_digest(self.payload_digest, "VersionedPluginEventEnvelope.payload_digest", required=False)
        for field_name in (
            "consumer_plugin_refs",
            "causality_refs",
            "policy_refs",
            "budget_refs",
            "evidence_refs",
            "provenance_refs",
        ):
            ensure_ref_items(getattr(self, field_name), f"VersionedPluginEventEnvelope.{field_name}")
        if not isinstance(self.audit_trace_envelope, L6AuditTraceEnvelope):
            raise ValueError("VersionedPluginEventEnvelope.audit_trace_envelope must be L6AuditTraceEnvelope")
        for field_name in ("calls_model", "invokes_tool", "writes_state", "direct_plugin_call", "carries_raw_payload", "action_replay_allowed"):
            ensure_bool(getattr(self, field_name), f"VersionedPluginEventEnvelope.{field_name}")
        if self.calls_model or self.invokes_tool or self.writes_state or self.direct_plugin_call or self.carries_raw_payload or self.action_replay_allowed:
            raise ValueError("L6 plugin event envelope is not execution, raw payload, direct plugin call, or action replay")
        ensure_schema_version(self.schema_version)

    @property
    def event_is_execution(self) -> bool:
        return False

    @property
    def event_replay_is_action_replay(self) -> bool:
        return False

    @property
    def digest(self) -> str:
        return stable_digest(self)
