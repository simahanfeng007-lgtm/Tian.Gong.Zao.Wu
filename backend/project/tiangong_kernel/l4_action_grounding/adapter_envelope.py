"""Adapter input, output, and failure envelopes."""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from .adapter_mode import AdapterMode
from .audit_requirement import AuditRequirementRef
from .cognitive_sink_hint import ActionResultCognitiveSinkHint
from .gate_result import ActionGroundingGateResult
from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text, ensure_true
from .permit_ref import ActionPermitRef
from .permit_scope import PermitScope


@dataclass(frozen=True, slots=True)
class AdapterObservationHint:
    """Observation hint for L3 re-planning; it is advisory only."""

    observation_ref: TypedRef
    summary: str = ""
    stability_hint: str = ""
    reversibility_hint: str = ""
    affective_hint: str = ""
    dynamic_drive_hint: str = ""
    math_hint: str = ""
    advisory_only: bool = True
    cannot_override_disabled: bool = True
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for value in (
            self.summary,
            self.stability_hint,
            self.reversibility_hint,
            self.affective_hint,
            self.dynamic_drive_hint,
            self.math_hint,
        ):
            ensure_short_text(value, "AdapterObservationHint text")
        ensure_true(self.advisory_only, "AdapterObservationHint.advisory_only")
        ensure_true(self.cannot_override_disabled, "AdapterObservationHint.cannot_override_disabled")
        ensure_schema_version(self.schema_version, "AdapterObservationHint.schema_version")


@dataclass(frozen=True, slots=True)
class AdapterInputEnvelope:
    """Input envelope from L3/L4 context to an adapter."""

    envelope_ref: TypedRef
    action_kind: str
    envelope_type: str = "adapter_input"
    mode: AdapterMode = AdapterMode.NO_OP
    source_request_ref: TypedRef | None = None
    source_step_ref: TypedRef | None = None
    requested_scope: PermitScope | None = None
    permit_ref: ActionPermitRef | None = None
    gate_result: ActionGroundingGateResult | None = None
    effect_intent_ref: TypedRef | None = None
    boundary_decision_ref: TypedRef | None = None
    lease_ref: TypedRef | None = None
    audit_requirement_ref: AuditRequirementRef | None = None
    resource_budget_ref: TypedRef | None = None
    credential_scope_ref: TypedRef | None = None
    sandbox_policy_ref: TypedRef | None = None
    payload_items: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    production_path: bool = False
    l3_controlled: bool = True
    l4_autonomous: bool = False
    contains_plain_credential: bool = False
    envelope_only: bool = True
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_short_text(self.action_kind, "AdapterInputEnvelope.action_kind", 128)
        ensure_short_text(self.envelope_type, "AdapterInputEnvelope.envelope_type", 128)
        for key, value in self.payload_items:
            ensure_short_text(key, "AdapterInputEnvelope.payload key", 128)
            ensure_short_text(value, "AdapterInputEnvelope.payload value")
        ensure_true(self.l3_controlled, "AdapterInputEnvelope.l3_controlled")
        ensure_false(self.l4_autonomous, "AdapterInputEnvelope.l4_autonomous")
        ensure_false(self.contains_plain_credential, "AdapterInputEnvelope.contains_plain_credential")
        ensure_true(self.envelope_only, "AdapterInputEnvelope.envelope_only")
        ensure_schema_version(self.schema_version, "AdapterInputEnvelope.schema_version")

    @property
    def production_source_chain_complete(self) -> bool:
        if not self.production_path:
            return True
        return all(
            ref is not None
            for ref in (
                self.source_request_ref,
                self.source_step_ref,
                self.gate_result,
                self.effect_intent_ref,
                self.boundary_decision_ref,
                self.lease_ref,
                self.audit_requirement_ref,
                self.resource_budget_ref,
                self.credential_scope_ref,
            )
        )


@dataclass(frozen=True, slots=True)
class AdapterOutputEnvelope:
    """Normalized adapter output; success can only be simulated/no-op/dry-run."""

    output_ref: TypedRef
    adapter_id: str
    adapter_kind: str
    action_kind: str
    mode: AdapterMode
    success: bool = False
    normalized_result_ref: TypedRef | None = None
    result_payload: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    observation_hint: AdapterObservationHint | None = None
    cognitive_sink_hint: ActionResultCognitiveSinkHint | None = None
    audit_requirement_ref: AuditRequirementRef | None = None
    evidence_ref: TypedRef | None = None
    resource_usage_preview: str = ""
    side_effect_summary: str = "none"
    reversibility_summary: str = "not_applicable"
    trace_ref: TypedRef | None = None
    created_at: str = ""
    real_action_performed: bool = False
    output_envelope_only: bool = True
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for value in (
            self.adapter_id,
            self.adapter_kind,
            self.action_kind,
            self.resource_usage_preview,
            self.side_effect_summary,
            self.reversibility_summary,
            self.created_at,
        ):
            ensure_short_text(value, "AdapterOutputEnvelope text")
        for key, value in self.result_payload:
            ensure_short_text(key, "AdapterOutputEnvelope.payload key", 128)
            ensure_short_text(value, "AdapterOutputEnvelope.payload value")
        ensure_false(self.real_action_performed, "AdapterOutputEnvelope.real_action_performed")
        ensure_true(self.output_envelope_only, "AdapterOutputEnvelope.output_envelope_only")
        ensure_schema_version(self.schema_version, "AdapterOutputEnvelope.schema_version")


@dataclass(frozen=True, slots=True)
class AdapterFailureEnvelope:
    """Normalized adapter failure; safe for L3 re-planning or stopping."""

    failure_ref: TypedRef
    adapter_id: str
    adapter_kind: str
    action_kind: str
    mode: AdapterMode
    failure_category: str
    failure_code: str
    message: str
    recoverability_hint: str = ""
    retry_allowed_hint: bool = False
    replan_required_hint: bool = True
    boundary_recheck_required_hint: bool = False
    audit_requirement_ref: AuditRequirementRef | None = None
    trace_ref: TypedRef | None = None
    created_at: str = ""
    real_action_performed: bool = False
    failure_envelope_only: bool = True
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for value in (
            self.adapter_id,
            self.adapter_kind,
            self.action_kind,
            self.failure_category,
            self.failure_code,
            self.message,
            self.recoverability_hint,
            self.created_at,
        ):
            ensure_short_text(value, "AdapterFailureEnvelope text")
        ensure_false(self.retry_allowed_hint, "AdapterFailureEnvelope.retry_allowed_hint")
        ensure_false(self.real_action_performed, "AdapterFailureEnvelope.real_action_performed")
        ensure_true(self.failure_envelope_only, "AdapterFailureEnvelope.failure_envelope_only")
        ensure_schema_version(self.schema_version, "AdapterFailureEnvelope.schema_version")


AdapterExecutionEnvelope = AdapterInputEnvelope
