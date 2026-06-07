"""L6 phase2 discovery, invocation request, and output return envelopes."""

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


class L6PluginOutputStatus(str, Enum):
    DECLARED_SUCCESS = "declared_success"
    DECLARED_FAILURE = "declared_failure"
    NEEDS_MODEL = "needs_model"
    NEEDS_TOOL = "needs_tool"
    EMITTED_PROJECTION = "emitted_projection"
    EMITTED_HANDOFF = "emitted_handoff"
    DEGRADED = "degraded"


@dataclass(frozen=True, slots=True)
class L6PluginDiscoverableProjection:
    discoverable_ref: str = "public:l6_discoverable_projection"
    plugin_ref: str = "l6:plugin_ref"
    manifest_ref: str = "ref:l6_manifest"
    lifecycle_state_ref: str = "lifecycle:l6_active_declared"
    public_capability_summary_refs: tuple[str, ...] = field(default_factory=lambda: ("summary:l6_capability",))
    requirement_summary_refs: tuple[str, ...] = field(default_factory=lambda: ("summary:l6_requirements",))
    callable_ref: str = ""
    contains_endpoint: bool = False
    contains_secret: bool = False
    contains_internal_plan: bool = False
    discoverable_is_invocable: bool = False
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for field_name in ("discoverable_ref", "plugin_ref", "manifest_ref", "lifecycle_state_ref"):
            ensure_ref_text(getattr(self, field_name), f"L6PluginDiscoverableProjection.{field_name}")
        ensure_ref_text(self.callable_ref, "L6PluginDiscoverableProjection.callable_ref", required=False)
        ensure_ref_items(self.public_capability_summary_refs, "L6PluginDiscoverableProjection.public_capability_summary_refs", required=True)
        ensure_ref_items(self.requirement_summary_refs, "L6PluginDiscoverableProjection.requirement_summary_refs", required=True)
        if self.callable_ref or self.contains_endpoint or self.contains_secret or self.contains_internal_plan or self.discoverable_is_invocable:
            raise ValueError("L6 discoverable projection is public metadata only, not callable or invocable")
        ensure_schema_version(self.schema_version)


@dataclass(frozen=True, slots=True)
class L3PluginCandidateView:
    candidate_view_ref: str = "l3:l6_plugin_candidate_view"
    discoverable_projection_ref: str = "public:l6_discoverable_projection"
    l5_host_registry_ref: str = "l5:l6_host_registry"
    candidate_selection_ref: str = "l3:l6_candidate_selection"
    public_projection_readonly: bool = True
    imports_l6_plugin: bool = False
    calls_l6_plugin: bool = False
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for field_name in ("candidate_view_ref", "discoverable_projection_ref", "l5_host_registry_ref", "candidate_selection_ref"):
            ensure_ref_text(getattr(self, field_name), f"L3PluginCandidateView.{field_name}")
        if not self.public_projection_readonly or self.imports_l6_plugin or self.calls_l6_plugin:
            raise ValueError("L3 candidate view can read public projection only and cannot import/call L6 plugin")
        ensure_schema_version(self.schema_version)


@dataclass(frozen=True, slots=True)
class L6PluginInvocationRequest:
    invocation_ref: str = "ref:l6_phase2_invocation"
    schema_version: str = L6_COMMON_SCHEMA_VERSION
    caller_layer: str = "L3_ORCHESTRATION"
    run_ref: str = "l3:run_ref"
    turn_ref: str = "l3:turn_ref"
    step_ref: str = "l3:step_ref"
    parent_trace_ref: str = "ref:l6_parent_trace"
    requested_plugin_ref: str = "l6:requested_plugin"
    plugin_manifest_ref: str = "ref:l6_manifest"
    requested_plugin_version_range_ref: str = "ref:l6_plugin_version_range"
    lifecycle_state_ref: str = "lifecycle:l6_active_declared"
    lifecycle_contract_version_ref: str = "ref:l6_lifecycle_contract_version"
    event_contract_version_range_ref: str = "event:l6_event_contract_range"
    projection_contract_version_range_ref: str = "projection:l6_projection_contract_range"
    handoff_contract_version_range_ref: str = "handoff:l6_handoff_contract_range"
    compatibility_matrix_ref: str = "ref:l6_compatibility_matrix"
    operation_ref: str = "ref:l6_operation"
    intent_ref: str = "ref:l6_intent"
    intent_summary: str = "summary:l6_invocation_intent"
    input_contract_ref: str = "ref:l6_input_contract"
    input_refs: tuple[str, ...] = field(default_factory=lambda: ("ref:l6_input",))
    context_minimization_profile_ref: str = "policy:l6_context_minimization"
    context_projection_refs: tuple[str, ...] = field(default_factory=tuple)
    state_projection_refs: tuple[str, ...] = field(default_factory=tuple)
    permission_requirement_refs: tuple[str, ...] = field(default_factory=lambda: ("permission:l6_permission_requirement",))
    budget_requirement_refs: tuple[str, ...] = field(default_factory=lambda: ("budget:l6_budget_requirement",))
    audit_requirement_refs: tuple[str, ...] = field(default_factory=lambda: ("audit:l6_audit_requirement",))
    credential_requirement_refs: tuple[str, ...] = field(default_factory=lambda: ("credential-policy:l6_credential_requirement",))
    context_requirement_refs: tuple[str, ...] = field(default_factory=lambda: ("context:l6_context_requirement",))
    model_capability_requirement_refs: tuple[str, ...] = field(default_factory=tuple)
    tool_capability_requirement_refs: tuple[str, ...] = field(default_factory=tuple)
    migration_requirement_ref: str = "migration:l6_migration_requirement"
    rollback_requirement_ref: str = "rollback:l6_rollback_requirement"
    replay_compatibility_requirement_ref: str = "ref:l6_replay_compatibility_requirement"
    hot_switch_readiness_requirement_ref: str = "hotswitch:l6_hot_switch_readiness_requirement"
    policy_refs: tuple[str, ...] = field(default_factory=lambda: ("policy:l6_l3_l5_required",))
    risk_refs: tuple[str, ...] = field(default_factory=lambda: ("ref:l6_risk_review",))
    human_gate_refs: tuple[str, ...] = field(default_factory=tuple)
    timeout_policy_ref: str = "policy:l6_timeout"
    retry_policy_ref: str = "policy:l6_retry"
    degradation_policy_ref: str = "policy:l6_degradation"
    idempotency_key_ref: str = "ref:l6_invocation_idempotency"
    authorization_ref: str = ""
    audit_trace_envelope: L6AuditTraceEnvelope = field(default_factory=L6AuditTraceEnvelope)
    evidence_refs: tuple[str, ...] = field(default_factory=lambda: ("evidence:l6_invocation",))
    responsibility_chain_ref: str = "responsibility:l6_invocation_chain"
    tamper_evidence_ref: str = "evidence:l6_invocation_tamper"
    safety_assertions: tuple[str, ...] = field(default_factory=lambda: ("ref:l6_invocation_no_direct_l4_l2",))
    imports_plugin: bool = False
    calls_plugin_directly: bool = False
    bypasses_l5_host: bool = False
    invokes_model: bool = False
    invokes_tool: bool = False
    writes_l2_state_fact: bool = False

    def __post_init__(self) -> None:
        ensure_schema_version(self.schema_version)
        if self.caller_layer != "L3_ORCHESTRATION":
            raise ValueError("L6PluginInvocationRequest.caller_layer must be L3_ORCHESTRATION")
        for field_name in (
            "invocation_ref",
            "run_ref",
            "turn_ref",
            "step_ref",
            "parent_trace_ref",
            "requested_plugin_ref",
            "plugin_manifest_ref",
            "requested_plugin_version_range_ref",
            "lifecycle_state_ref",
            "lifecycle_contract_version_ref",
            "event_contract_version_range_ref",
            "projection_contract_version_range_ref",
            "handoff_contract_version_range_ref",
            "compatibility_matrix_ref",
            "operation_ref",
            "intent_ref",
            "input_contract_ref",
            "context_minimization_profile_ref",
            "migration_requirement_ref",
            "rollback_requirement_ref",
            "replay_compatibility_requirement_ref",
            "hot_switch_readiness_requirement_ref",
            "timeout_policy_ref",
            "retry_policy_ref",
            "degradation_policy_ref",
            "idempotency_key_ref",
            "responsibility_chain_ref",
            "tamper_evidence_ref",
        ):
            ensure_ref_text(getattr(self, field_name), f"L6PluginInvocationRequest.{field_name}")
        ensure_ref_text(self.authorization_ref, "L6PluginInvocationRequest.authorization_ref", required=False)
        ensure_no_live_or_sensitive_text(self.intent_summary, "L6PluginInvocationRequest.intent_summary")
        for field_name in (
            "input_refs",
            "context_projection_refs",
            "state_projection_refs",
            "permission_requirement_refs",
            "budget_requirement_refs",
            "audit_requirement_refs",
            "credential_requirement_refs",
            "context_requirement_refs",
            "model_capability_requirement_refs",
            "tool_capability_requirement_refs",
            "policy_refs",
            "risk_refs",
            "human_gate_refs",
            "evidence_refs",
            "safety_assertions",
        ):
            ensure_ref_items(getattr(self, field_name), f"L6PluginInvocationRequest.{field_name}", required=field_name in {"input_refs", "permission_requirement_refs", "budget_requirement_refs", "audit_requirement_refs", "credential_requirement_refs", "context_requirement_refs", "policy_refs", "evidence_refs", "safety_assertions"})
        if not isinstance(self.audit_trace_envelope, L6AuditTraceEnvelope):
            raise ValueError("L6PluginInvocationRequest.audit_trace_envelope must be L6AuditTraceEnvelope")
        if any((self.imports_plugin, self.calls_plugin_directly, self.bypasses_l5_host, self.invokes_model, self.invokes_tool, self.writes_l2_state_fact)):
            raise ValueError("L6 invocation request is a governed envelope, not direct import/call/provider/tool/state access")

    @property
    def discoverable_is_invocable(self) -> bool:
        return False

    @property
    def active_is_authorized(self) -> bool:
        return False

    @property
    def digest(self) -> str:
        return stable_digest(self)


@dataclass(frozen=True, slots=True)
class L6PluginOutputReturnEnvelope:
    output_return_ref: str = "ref:l6_output_return"
    invocation_ref: str = "ref:l6_phase2_invocation"
    plugin_ref: str = "l6:plugin_ref"
    plugin_version_ref: str = "ref:l6_plugin_version"
    output_schema_version: str = L6_COMMON_SCHEMA_VERSION
    output_contract_version: str = "ref:l6_output_contract_version"
    status: L6PluginOutputStatus | str = L6PluginOutputStatus.DECLARED_SUCCESS
    output_kind: str = "summary:l6_output_kind"
    result_summary_ref: str = "summary:l6_result_summary"
    result_digest: str = ""
    event_publication_refs: tuple[str, ...] = field(default_factory=tuple)
    state_projection_refs: tuple[str, ...] = field(default_factory=tuple)
    handoff_refs: tuple[str, ...] = field(default_factory=tuple)
    model_capability_requirement_refs: tuple[str, ...] = field(default_factory=tuple)
    tool_capability_requirement_refs: tuple[str, ...] = field(default_factory=tuple)
    context_request_refs: tuple[str, ...] = field(default_factory=tuple)
    human_gate_request_refs: tuple[str, ...] = field(default_factory=tuple)
    migration_advice_refs: tuple[str, ...] = field(default_factory=tuple)
    rollback_advice_refs: tuple[str, ...] = field(default_factory=tuple)
    hot_switch_readiness_refs: tuple[str, ...] = field(default_factory=tuple)
    replay_compatibility_refs: tuple[str, ...] = field(default_factory=tuple)
    breaking_change_warning_refs: tuple[str, ...] = field(default_factory=tuple)
    failure_refs: tuple[str, ...] = field(default_factory=tuple)
    degradation_refs: tuple[str, ...] = field(default_factory=tuple)
    risk_hints: tuple[str, ...] = field(default_factory=tuple)
    budget_usage_summary: str = "summary:l6_budget_usage_no_decrement"
    audit_requirement_ref: str = "audit:l6_output_audit_requirement"
    audit_ref: str = "audit:l6_output_audit_ref"
    evidence_refs: tuple[str, ...] = field(default_factory=lambda: ("evidence:l6_output",))
    provenance_refs: tuple[str, ...] = field(default_factory=lambda: ("evidence:l6_output_provenance",))
    trace_ref: str = "ref:l6_output_trace"
    responsibility_chain_ref: str = "responsibility:l6_output_chain"
    accountability_ref: str = "responsibility:l6_output_accountability"
    redaction_profile_ref: str = "policy:l6_output_redaction"
    public_projection_ref: str = "public:l6_output_projection"
    host_validation_ref: str = "l5:l6_output_host_validation"
    tamper_evidence_ref: str = "evidence:l6_output_tamper"
    next_step_suggestion_refs: tuple[str, ...] = field(default_factory=tuple)
    safety_assertions: tuple[str, ...] = field(default_factory=lambda: ("ref:l6_output_requirement_not_execution",))
    digest_ref: str = "digest:l6_output_digest"
    calls_model: bool = False
    invokes_tool: bool = False
    calls_l4_adapter: bool = False
    writes_l2_state_fact: bool = False
    decrements_budget: bool = False
    writes_audit_record: bool = False
    suggestion_is_command: bool = False
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for field_name in (
            "output_return_ref",
            "invocation_ref",
            "plugin_ref",
            "plugin_version_ref",
            "output_contract_version",
            "output_kind",
            "result_summary_ref",
            "audit_requirement_ref",
            "audit_ref",
            "trace_ref",
            "responsibility_chain_ref",
            "accountability_ref",
            "redaction_profile_ref",
            "public_projection_ref",
            "host_validation_ref",
            "tamper_evidence_ref",
            "digest_ref",
        ):
            ensure_ref_text(getattr(self, field_name), f"L6PluginOutputReturnEnvelope.{field_name}")
        ensure_schema_version(self.output_schema_version, "output_schema_version")
        object.__setattr__(self, "status", L6PluginOutputStatus(self.status))
        ensure_digest(self.result_digest, "L6PluginOutputReturnEnvelope.result_digest", required=False)
        ensure_no_live_or_sensitive_text(self.budget_usage_summary, "L6PluginOutputReturnEnvelope.budget_usage_summary")
        for field_name in (
            "event_publication_refs",
            "state_projection_refs",
            "handoff_refs",
            "model_capability_requirement_refs",
            "tool_capability_requirement_refs",
            "context_request_refs",
            "human_gate_request_refs",
            "migration_advice_refs",
            "rollback_advice_refs",
            "hot_switch_readiness_refs",
            "replay_compatibility_refs",
            "breaking_change_warning_refs",
            "failure_refs",
            "degradation_refs",
            "risk_hints",
            "evidence_refs",
            "provenance_refs",
            "next_step_suggestion_refs",
            "safety_assertions",
        ):
            ensure_ref_items(getattr(self, field_name), f"L6PluginOutputReturnEnvelope.{field_name}")
        if any((self.calls_model, self.invokes_tool, self.calls_l4_adapter, self.writes_l2_state_fact, self.decrements_budget, self.writes_audit_record, self.suggestion_is_command)):
            raise ValueError("L6 output return carries requirements/projections/handoffs only; it cannot execute or command")
        ensure_schema_version(self.schema_version)

    @property
    def output_requirement_is_execution(self) -> bool:
        return False

    @property
    def digest(self) -> str:
        return stable_digest(self)
