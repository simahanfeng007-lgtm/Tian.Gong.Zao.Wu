"""L6 phase2 state projection and context/belief/world envelopes."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from ._common import (
    ensure_score,
    L6_COMMON_SCHEMA_VERSION,
    ensure_bool, ensure_score,
    ensure_digest,
    ensure_no_live_or_sensitive_text,
    ensure_ref_items,
    ensure_ref_text,
    ensure_schema_version,
    stable_digest,
)
from .audit import L6AuditTraceEnvelope


class L6ProjectionKind(str, Enum):
    CONTEXT = "context_projection"
    BELIEF_CANDIDATE = "belief_candidate_projection"
    WORLD_CANDIDATE = "world_candidate_projection"
    CONTEXT_SAFETY = "context_safety_projection"
    HANDOFF = "handoff_projection"
    ACTOR_COLLABORATION = "actor_collaboration_projection"
    RESULT_AGGREGATION = "result_aggregation_projection"
    LIFECYCLE = "lifecycle_projection"
    ADMISSION = "admission_projection"
    VERSION_GOVERNANCE = "version_governance_projection"


@dataclass(frozen=True, slots=True)
class VersionedStateProjectionEnvelope:
    projection_ref: str = "projection:l6_phase2_projection"
    projection_kind: L6ProjectionKind | str = L6ProjectionKind.CONTEXT
    projection_schema_version: str = L6_COMMON_SCHEMA_VERSION
    projection_contract_version: str = "ref:l6_phase2_projection_contract_version"
    source_plugin_ref: str = "l6:source_plugin"
    producer_plugin_version_ref: str = "ref:l6_projection_producer_version"
    target_state_kind_ref: str = "state:l6_target_state_kind"
    source_event_refs: tuple[str, ...] = field(default_factory=lambda: ("event:l6_projection_source_event",))
    source_handoff_refs: tuple[str, ...] = field(default_factory=tuple)
    source_context_refs: tuple[str, ...] = field(default_factory=tuple)
    source_evidence_refs: tuple[str, ...] = field(default_factory=lambda: ("evidence:l6_projection_evidence",))
    projection_payload_schema_ref: str = "projection:l6_payload_schema"
    projection_summary: str = "summary:l6_phase2_projection_summary"
    projection_digest: str = ""
    projection_status: str = "summary:candidate"
    candidate_or_fact_hint: str = "summary:candidate_only"
    candidate_only: bool = True
    canonical_fact: bool = False
    l2_fact_binding_policy_ref: str = "policy:l6_no_direct_l2_fact_binding"
    l2_write_allowed: bool = False
    ttl_ref: str = "ref:l6_projection_ttl"
    expiry_ref: str = "ref:l6_projection_expiry"
    expiration_policy_ref: str = "policy:l6_projection_expiration"
    conflict_policy_ref: str = "policy:l6_projection_conflict"
    revocation_policy_ref: str = "policy:l6_projection_revocation"
    rollback_policy_ref: str = "rollback:l6_projection_rollback"
    migration_policy_ref: str = "migration:l6_projection_migration"
    upcast_policy_ref: str = "policy:l6_projection_upcast"
    replay_compatibility_ref: str = "ref:l6_projection_replay_compatibility"
    confidence_score: float = 0.5
    risk_tags: tuple[str, ...] = field(default_factory=lambda: ("summary:l6_projection_risk_review",))
    redaction_policy_ref: str = "policy:l6_projection_redaction"
    audit_trace_envelope: L6AuditTraceEnvelope = field(default_factory=L6AuditTraceEnvelope)
    evidence_refs: tuple[str, ...] = field(default_factory=lambda: ("evidence:l6_projection_evidence",))
    provenance_refs: tuple[str, ...] = field(default_factory=lambda: ("evidence:l6_projection_provenance",))
    trace_ref: str = "ref:l6_projection_trace"
    responsibility_chain_ref: str = "responsibility:l6_projection_chain"
    accountability_ref: str = "responsibility:l6_projection_accountability"
    tamper_evidence_ref: str = "evidence:l6_projection_tamper"
    public_projection_ref: str = "public:l6_projection_public"
    writes_l2_state_fact: bool = False
    mutates_core_state: bool = False
    modifies_memory: bool = False
    modifies_affective_state: bool = False
    modifies_budget: bool = False
    modifies_audit: bool = False
    reads_credential: bool = False
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.projection_ref, "VersionedStateProjectionEnvelope.projection_ref")
        object.__setattr__(self, "projection_kind", L6ProjectionKind(self.projection_kind))
        ensure_schema_version(self.projection_schema_version, "projection_schema_version")
        for field_name in (
            "projection_contract_version",
            "source_plugin_ref",
            "producer_plugin_version_ref",
            "target_state_kind_ref",
            "projection_payload_schema_ref",
            "l2_fact_binding_policy_ref",
            "ttl_ref",
            "expiry_ref",
            "expiration_policy_ref",
            "conflict_policy_ref",
            "revocation_policy_ref",
            "rollback_policy_ref",
            "migration_policy_ref",
            "upcast_policy_ref",
            "replay_compatibility_ref",
            "redaction_policy_ref",
            "trace_ref",
            "responsibility_chain_ref",
            "accountability_ref",
            "tamper_evidence_ref",
            "public_projection_ref",
        ):
            ensure_ref_text(getattr(self, field_name), f"VersionedStateProjectionEnvelope.{field_name}")
        for field_name in (
            "source_event_refs",
            "source_handoff_refs",
            "source_context_refs",
            "source_evidence_refs",
            "risk_tags",
            "evidence_refs",
            "provenance_refs",
        ):
            ensure_ref_items(getattr(self, field_name), f"VersionedStateProjectionEnvelope.{field_name}")
        for field_name in ("projection_summary", "projection_status", "candidate_or_fact_hint"):
            ensure_no_live_or_sensitive_text(getattr(self, field_name), f"VersionedStateProjectionEnvelope.{field_name}")
        ensure_digest(self.projection_digest, "VersionedStateProjectionEnvelope.projection_digest", required=False)
        ensure_score(self.confidence_score, "VersionedStateProjectionEnvelope.confidence_score")
        if not isinstance(self.audit_trace_envelope, L6AuditTraceEnvelope):
            raise ValueError("VersionedStateProjectionEnvelope.audit_trace_envelope must be L6AuditTraceEnvelope")
        for field_name in (
            "candidate_only",
            "canonical_fact",
            "l2_write_allowed",
            "writes_l2_state_fact",
            "mutates_core_state",
            "modifies_memory",
            "modifies_affective_state",
            "modifies_budget",
            "modifies_audit",
            "reads_credential",
        ):
            ensure_bool(getattr(self, field_name), f"VersionedStateProjectionEnvelope.{field_name}")
        if not self.candidate_only or self.canonical_fact or self.l2_write_allowed:
            raise ValueError("L6 projection must remain candidate-only and cannot become L2 fact")
        if any(
            (
                self.writes_l2_state_fact,
                self.mutates_core_state,
                self.modifies_memory,
                self.modifies_affective_state,
                self.modifies_budget,
                self.modifies_audit,
                self.reads_credential,
            )
        ):
            raise ValueError("L6 projection cannot directly mutate state, audit, budget, memory, affective state, or credentials")
        ensure_schema_version(self.schema_version)

    @property
    def projection_is_l2_fact(self) -> bool:
        return False

    @property
    def has_expiry_conflict_revocation_rollback(self) -> bool:
        return bool(self.ttl_ref and self.expiry_ref and self.conflict_policy_ref and self.revocation_policy_ref and self.rollback_policy_ref)

    @property
    def digest(self) -> str:
        return stable_digest(self)


@dataclass(frozen=True, slots=True)
class ContextRequirement:
    requirement_ref: str = "context:l6_phase2_context_requirement"
    minimization_profile_ref: str = "policy:l6_context_minimization"
    safety_projection_required_ref: str = "projection:l6_context_safety_required"
    requirement_only: bool = True
    injects_prompt: bool = False
    reads_private_context: bool = False
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.requirement_ref, "ContextRequirement.requirement_ref")
        ensure_ref_text(self.minimization_profile_ref, "ContextRequirement.minimization_profile_ref")
        ensure_ref_text(self.safety_projection_required_ref, "ContextRequirement.safety_projection_required_ref")
        if not self.requirement_only or self.injects_prompt or self.reads_private_context:
            raise ValueError("L6 context requirement is not prompt injection or private context access")
        ensure_schema_version(self.schema_version)


@dataclass(frozen=True, slots=True)
class BeliefRequirement:
    requirement_ref: str = "context:l6_phase2_belief_requirement"
    candidate_projection_required_ref: str = "projection:l6_belief_candidate_required"
    requirement_only: bool = True
    writes_belief_fact: bool = False
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.requirement_ref, "BeliefRequirement.requirement_ref")
        ensure_ref_text(self.candidate_projection_required_ref, "BeliefRequirement.candidate_projection_required_ref")
        if not self.requirement_only or self.writes_belief_fact:
            raise ValueError("L6 belief requirement cannot write belief fact")
        ensure_schema_version(self.schema_version)


@dataclass(frozen=True, slots=True)
class WorldRequirement:
    requirement_ref: str = "context:l6_phase2_world_requirement"
    candidate_projection_required_ref: str = "projection:l6_world_candidate_required"
    requirement_only: bool = True
    writes_world_fact: bool = False
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.requirement_ref, "WorldRequirement.requirement_ref")
        ensure_ref_text(self.candidate_projection_required_ref, "WorldRequirement.candidate_projection_required_ref")
        if not self.requirement_only or self.writes_world_fact:
            raise ValueError("L6 world requirement cannot write world fact")
        ensure_schema_version(self.schema_version)


@dataclass(frozen=True, slots=True)
class ContextView:
    context_view_ref: str = "context:l6_phase2_context_view"
    source_projection_refs: tuple[str, ...] = field(default_factory=lambda: ("projection:l6_context_projection",))
    redaction_policy_ref: str = "policy:l6_context_view_redaction"
    prompt_injection_allowed: bool = False
    raw_context_allowed: bool = False
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.context_view_ref, "ContextView.context_view_ref")
        ensure_ref_items(self.source_projection_refs, "ContextView.source_projection_refs", required=True)
        ensure_ref_text(self.redaction_policy_ref, "ContextView.redaction_policy_ref")
        if self.prompt_injection_allowed or self.raw_context_allowed:
            raise ValueError("L6 context view cannot become prompt injection or raw context")
        ensure_schema_version(self.schema_version)


@dataclass(frozen=True, slots=True)
class ContextProjection(VersionedStateProjectionEnvelope):
    projection_kind: L6ProjectionKind | str = L6ProjectionKind.CONTEXT
    is_prompt: bool = False
    context_injection_permit: bool = False

    def __post_init__(self) -> None:
        VersionedStateProjectionEnvelope.__post_init__(self)
        if self.is_prompt or self.context_injection_permit:
            raise ValueError("L6 ContextProjection is not prompt or context injection permit")


@dataclass(frozen=True, slots=True)
class BeliefCandidateProjection(VersionedStateProjectionEnvelope):
    projection_kind: L6ProjectionKind | str = L6ProjectionKind.BELIEF_CANDIDATE
    event_fact: bool = False
    overwrites_event: bool = False

    def __post_init__(self) -> None:
        VersionedStateProjectionEnvelope.__post_init__(self)
        if self.event_fact or self.overwrites_event:
            raise ValueError("L6 BeliefCandidateProjection is not event fact and cannot overwrite events")


@dataclass(frozen=True, slots=True)
class WorldCandidateProjection(VersionedStateProjectionEnvelope):
    projection_kind: L6ProjectionKind | str = L6ProjectionKind.WORLD_CANDIDATE
    canonical_world_state: bool = False

    def __post_init__(self) -> None:
        VersionedStateProjectionEnvelope.__post_init__(self)
        if self.canonical_world_state:
            raise ValueError("L6 WorldCandidateProjection is not canonical world state")


@dataclass(frozen=True, slots=True)
class ContextSafetyProjection(VersionedStateProjectionEnvelope):
    projection_kind: L6ProjectionKind | str = L6ProjectionKind.CONTEXT_SAFETY
    tool_output_demoted: bool = True
    model_output_demoted: bool = True
    instruction_boundary_preserved: bool = True
    direct_model_context_injection: bool = False

    def __post_init__(self) -> None:
        VersionedStateProjectionEnvelope.__post_init__(self)
        if not self.tool_output_demoted or not self.model_output_demoted or not self.instruction_boundary_preserved:
            raise ValueError("L6 ContextSafetyProjection must demote tool/model output and preserve instruction boundary")
        if self.direct_model_context_injection:
            raise ValueError("L6 ContextSafetyProjection cannot directly inject model context")


@dataclass(frozen=True, slots=True)
class HandoffProjection(VersionedStateProjectionEnvelope):
    projection_kind: L6ProjectionKind | str = L6ProjectionKind.HANDOFF


@dataclass(frozen=True, slots=True)
class ActorCollaborationProjection(VersionedStateProjectionEnvelope):
    projection_kind: L6ProjectionKind | str = L6ProjectionKind.ACTOR_COLLABORATION


@dataclass(frozen=True, slots=True)
class ResultAggregationProjection(VersionedStateProjectionEnvelope):
    projection_kind: L6ProjectionKind | str = L6ProjectionKind.RESULT_AGGREGATION
    auto_merge: bool = False

    def __post_init__(self) -> None:
        VersionedStateProjectionEnvelope.__post_init__(self)
        if self.auto_merge:
            raise ValueError("L6 result aggregation projection cannot auto-merge")


@dataclass(frozen=True, slots=True)
class ContextBeliefWorldHandoffEnvelope:
    envelope_ref: str = "handoff:l6_phase2_context_belief_world"
    context_projection_ref: str = "projection:l6_context_projection"
    belief_candidate_projection_ref: str = "projection:l6_belief_candidate_projection"
    world_candidate_projection_ref: str = "projection:l6_world_candidate_projection"
    context_safety_projection_ref: str = "projection:l6_context_safety_projection"
    l5_review_ref: str = "l5:l6_context_belief_world_review"
    l3_reentry_ref: str = "l3:l6_context_belief_world_reentry"
    writes_l2_state_fact: bool = False
    direct_context_injection: bool = False
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for field_name in (
            "envelope_ref",
            "context_projection_ref",
            "belief_candidate_projection_ref",
            "world_candidate_projection_ref",
            "context_safety_projection_ref",
            "l5_review_ref",
            "l3_reentry_ref",
        ):
            ensure_ref_text(getattr(self, field_name), f"ContextBeliefWorldHandoffEnvelope.{field_name}")
        if self.writes_l2_state_fact or self.direct_context_injection:
            raise ValueError("L6 context/belief/world handoff cannot write L2 or directly inject context")
        ensure_schema_version(self.schema_version)
