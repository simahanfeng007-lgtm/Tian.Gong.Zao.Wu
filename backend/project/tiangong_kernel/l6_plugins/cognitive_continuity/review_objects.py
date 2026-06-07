"""L6 phase4 supplemental review objects from full specialist planning pack.

All classes in this module are inert review/projection/candidate objects.  They
never mutate L2 facts, memory, audit stores, budgets, credentials, or external
systems.  The module exists to close the gap between the first phase4 package
and the later full phase4 planning pack.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l6_plugins.common._common import ensure_bool, ensure_score, ensure_ref_items, ensure_ref_text, ensure_no_live_or_sensitive_text
from .common import CognitiveOutputKind
from .projection import CognitiveOutputBase


def _score(value: float, field_name: str) -> None:
    ensure_score(value, field_name)


@dataclass(frozen=True)
class ContextGapReport(CognitiveOutputBase):
    output_ref: str = "projection:l6_phase4_context_gap_report"
    output_kind: CognitiveOutputKind | str = CognitiveOutputKind.REPORT
    plugin_ref: str = "l6_phase4:context_continuity"
    gap_refs: tuple[str, ...] = field(default_factory=lambda: ("ref:l6_phase4_context_gap",))
    context_reentry_required: bool = True
    prompt_injection_allowed: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.gap_refs, "ContextGapReport.gap_refs", required=True)
        ensure_bool(self.context_reentry_required, "ContextGapReport.context_reentry_required")
        ensure_bool(self.prompt_injection_allowed, "ContextGapReport.prompt_injection_allowed")
        if not self.context_reentry_required or self.prompt_injection_allowed:
            raise ValueError("context gap report must stay review mediated and cannot inject prompt")


@dataclass(frozen=True)
class ContextPollutionRiskProjection(CognitiveOutputBase):
    output_ref: str = "projection:l6_phase4_context_pollution_risk"
    plugin_ref: str = "l6_phase4:context_continuity"
    pollution_risk_score: float = 0.0
    compression_required: bool = True
    raw_context_exposed: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        _score(self.pollution_risk_score, "ContextPollutionRiskProjection.pollution_risk_score")
        ensure_bool(self.compression_required, "ContextPollutionRiskProjection.compression_required")
        ensure_bool(self.raw_context_exposed, "ContextPollutionRiskProjection.raw_context_exposed")
        if self.raw_context_exposed:
            raise ValueError("context pollution projection cannot expose raw context")


@dataclass(frozen=True)
class BeliefReviewEnvelope(CognitiveOutputBase):
    output_ref: str = "projection:l6_phase4_belief_review_envelope"
    output_kind: CognitiveOutputKind | str = CognitiveOutputKind.REVIEW_REQUEST
    plugin_ref: str = "l6_phase4:belief_world_review"
    belief_candidate_refs: tuple[str, ...] = field(default_factory=lambda: ("projection:l6_phase4_belief_candidate",))
    event_refs: tuple[str, ...] = field(default_factory=lambda: ("event:l6_phase4_belief_source_event",))
    event_precedence_status_ref: str = "review:l6_phase4_belief_event_precedence"
    evidence_missing: bool = False
    fact_write_allowed: bool = False
    overrides_event: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.belief_candidate_refs, "BeliefReviewEnvelope.belief_candidate_refs", required=True)
        ensure_ref_items(self.event_refs, "BeliefReviewEnvelope.event_refs", required=True)
        ensure_ref_text(self.event_precedence_status_ref, "BeliefReviewEnvelope.event_precedence_status_ref")
        ensure_bool(self.evidence_missing, "BeliefReviewEnvelope.evidence_missing")
        ensure_bool(self.fact_write_allowed, "BeliefReviewEnvelope.fact_write_allowed")
        ensure_bool(self.overrides_event, "BeliefReviewEnvelope.overrides_event")
        if self.fact_write_allowed or self.overrides_event:
            raise ValueError("belief review envelope cannot write fact or override event precedence")


@dataclass(frozen=True)
class BeliefConflictReport(CognitiveOutputBase):
    output_ref: str = "projection:l6_phase4_belief_conflict_report"
    output_kind: CognitiveOutputKind | str = CognitiveOutputKind.REPORT
    plugin_ref: str = "l6_phase4:belief_world_review"
    conflict_refs: tuple[str, ...] = field(default_factory=lambda: ("ref:l6_phase4_belief_conflict",))
    revision_required: bool = True
    overrides_user_request: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.conflict_refs, "BeliefConflictReport.conflict_refs", required=True)
        ensure_bool(self.revision_required, "BeliefConflictReport.revision_required")
        ensure_bool(self.overrides_user_request, "BeliefConflictReport.overrides_user_request")
        if self.overrides_user_request:
            raise ValueError("belief conflict report cannot override explicit user request")


@dataclass(frozen=True)
class WorldReviewEnvelope(CognitiveOutputBase):
    output_ref: str = "projection:l6_phase4_world_review_envelope"
    output_kind: CognitiveOutputKind | str = CognitiveOutputKind.REVIEW_REQUEST
    plugin_ref: str = "l6_phase4:belief_world_review"
    world_candidate_refs: tuple[str, ...] = field(default_factory=lambda: ("projection:l6_phase4_world_candidate",))
    observed_at_ref: str = "event:l6_phase4_world_observed_at"
    expires_at_ref: str = "ref:l6_phase4_world_expires_at"
    staleness_policy_ref: str = "policy:l6_phase4_world_staleness"
    trust_boundary_ref: str = "policy:l6_phase4_world_trust_boundary"
    freshness_status_ref: str = "review:l6_phase4_world_freshness"
    canonicalization_suggestion_only: bool = True
    canonical_state_write_allowed: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.world_candidate_refs, "WorldReviewEnvelope.world_candidate_refs", required=True)
        for field_name in ("observed_at_ref", "expires_at_ref", "staleness_policy_ref", "trust_boundary_ref", "freshness_status_ref"):
            ensure_ref_text(getattr(self, field_name), f"WorldReviewEnvelope.{field_name}")
        ensure_bool(self.canonicalization_suggestion_only, "WorldReviewEnvelope.canonicalization_suggestion_only")
        ensure_bool(self.canonical_state_write_allowed, "WorldReviewEnvelope.canonical_state_write_allowed")
        if not self.canonicalization_suggestion_only or self.canonical_state_write_allowed:
            raise ValueError("world review envelope cannot canonicalize or write state")


@dataclass(frozen=True)
class WorldConflictReport(CognitiveOutputBase):
    output_ref: str = "projection:l6_phase4_world_conflict_report"
    output_kind: CognitiveOutputKind | str = CognitiveOutputKind.REPORT
    plugin_ref: str = "l6_phase4:belief_world_review"
    conflict_refs: tuple[str, ...] = field(default_factory=lambda: ("ref:l6_phase4_world_conflict",))
    l5_policy_review_required: bool = True

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.conflict_refs, "WorldConflictReport.conflict_refs", required=True)
        ensure_bool(self.l5_policy_review_required, "WorldConflictReport.l5_policy_review_required")
        if not self.l5_policy_review_required:
            raise ValueError("world conflict report must require L5 policy review")


@dataclass(frozen=True)
class WorldStalenessReport(CognitiveOutputBase):
    output_ref: str = "projection:l6_phase4_world_staleness_report"
    output_kind: CognitiveOutputKind | str = CognitiveOutputKind.REPORT
    plugin_ref: str = "l6_phase4:belief_world_review"
    stale_candidate_refs: tuple[str, ...] = field(default_factory=lambda: ("projection:l6_phase4_stale_world_candidate",))
    refresh_requirement_ref: str = "ref:l6_phase4_world_refresh_requirement"
    direct_refresh_allowed: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.stale_candidate_refs, "WorldStalenessReport.stale_candidate_refs", required=True)
        ensure_ref_text(self.refresh_requirement_ref, "WorldStalenessReport.refresh_requirement_ref")
        ensure_bool(self.direct_refresh_allowed, "WorldStalenessReport.direct_refresh_allowed")
        if self.direct_refresh_allowed:
            raise ValueError("world staleness report cannot directly refresh")


@dataclass(frozen=True)
class WorldConstraintReviewProjection(CognitiveOutputBase):
    output_ref: str = "projection:l6_phase4_world_constraint_review"
    plugin_ref: str = "l6_phase4:belief_world_review"
    constraint_strength_score: float = 0.5
    legal_decision_allowed: bool = False
    permission_decision_allowed: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        _score(self.constraint_strength_score, "WorldConstraintReviewProjection.constraint_strength_score")
        ensure_bool(self.legal_decision_allowed, "WorldConstraintReviewProjection.legal_decision_allowed")
        ensure_bool(self.permission_decision_allowed, "WorldConstraintReviewProjection.permission_decision_allowed")
        if self.legal_decision_allowed or self.permission_decision_allowed:
            raise ValueError("world constraint review cannot be legal or permission decision")


@dataclass(frozen=True)
class CandidateFactProposal(CognitiveOutputBase):
    output_ref: str = "projection:l6_phase4_candidate_fact_proposal"
    output_kind: CognitiveOutputKind | str = CognitiveOutputKind.CANDIDATE
    plugin_ref: str = "l6_phase4:belief_world_review"
    claim_digest_ref: str = "digest:l6_phase4_candidate_fact_claim"
    fact_domain_ref: str = "fact:l6_phase4_candidate_domain"
    source_projection_refs: tuple[str, ...] = field(default_factory=lambda: ("projection:l6_phase4_belief_world_review",))
    conflict_refs: tuple[str, ...] = field(default_factory=tuple)
    freshness_status_ref: str = "review:l6_phase4_candidate_fact_freshness"
    candidate_only: bool = True
    canonical_fact: bool = False
    l2_write_allowed: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_text(self.claim_digest_ref, "CandidateFactProposal.claim_digest_ref")
        ensure_ref_text(self.fact_domain_ref, "CandidateFactProposal.fact_domain_ref")
        ensure_ref_items(self.source_projection_refs, "CandidateFactProposal.source_projection_refs", required=True)
        ensure_ref_items(self.conflict_refs, "CandidateFactProposal.conflict_refs")
        ensure_ref_text(self.freshness_status_ref, "CandidateFactProposal.freshness_status_ref")
        for field_name in ("candidate_only", "canonical_fact", "l2_write_allowed"):
            ensure_bool(getattr(self, field_name), f"CandidateFactProposal.{field_name}")
        if not self.candidate_only or self.canonical_fact or self.l2_write_allowed:
            raise ValueError("candidate fact proposal is candidate-only and cannot write L2 fact")


@dataclass(frozen=True)
class CandidateFactReviewEnvelope(CognitiveOutputBase):
    output_ref: str = "projection:l6_phase4_candidate_fact_review_envelope"
    output_kind: CognitiveOutputKind | str = CognitiveOutputKind.REVIEW_REQUEST
    plugin_ref: str = "l6_phase4:belief_world_review"
    candidate_fact_ref: str = "projection:l6_phase4_candidate_fact"
    l2_admission_candidate_only: bool = True
    l2_fact_write_allowed: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_text(self.candidate_fact_ref, "CandidateFactReviewEnvelope.candidate_fact_ref")
        ensure_bool(self.l2_admission_candidate_only, "CandidateFactReviewEnvelope.l2_admission_candidate_only")
        ensure_bool(self.l2_fact_write_allowed, "CandidateFactReviewEnvelope.l2_fact_write_allowed")
        if not self.l2_admission_candidate_only or self.l2_fact_write_allowed:
            raise ValueError("candidate fact review envelope cannot write L2 fact")


@dataclass(frozen=True)
class MemoryContextSafetyProjection(CognitiveOutputBase):
    output_ref: str = "projection:l6_phase4_memory_context_safety"
    plugin_ref: str = "l6_phase4:memory_candidate"
    memory_candidate_refs: tuple[str, ...] = field(default_factory=lambda: ("projection:l6_phase4_memory_candidate",))
    safe_for_context_summary: bool = True
    direct_prompt_injection_allowed: bool = False
    privacy_filter_required: bool = True

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.memory_candidate_refs, "MemoryContextSafetyProjection.memory_candidate_refs", required=True)
        for field_name in ("safe_for_context_summary", "direct_prompt_injection_allowed", "privacy_filter_required"):
            ensure_bool(getattr(self, field_name), f"MemoryContextSafetyProjection.{field_name}")
        if self.direct_prompt_injection_allowed:
            raise ValueError("memory context safety projection cannot permit prompt injection")


@dataclass(frozen=True)
class MemoryUpdateProposalReviewCandidate(CognitiveOutputBase):
    output_ref: str = "projection:l6_phase4_memory_update_review_candidate"
    output_kind: CognitiveOutputKind | str = CognitiveOutputKind.CANDIDATE
    plugin_ref: str = "l6_phase4:memory_candidate"
    update_summary_ref: str = "summary:l6_phase4_memory_update_candidate"
    consent_requirement_ref: str = "policy:l6_phase4_memory_consent_requirement"
    writes_memory: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_text(self.update_summary_ref, "MemoryUpdateProposalReviewCandidate.update_summary_ref")
        ensure_ref_text(self.consent_requirement_ref, "MemoryUpdateProposalReviewCandidate.consent_requirement_ref")
        ensure_bool(self.writes_memory, "MemoryUpdateProposalReviewCandidate.writes_memory")
        if self.writes_memory:
            raise ValueError("memory update proposal review candidate cannot write memory")


@dataclass(frozen=True)
class MemoryConflictReport(CognitiveOutputBase):
    output_ref: str = "projection:l6_phase4_memory_conflict_report"
    output_kind: CognitiveOutputKind | str = CognitiveOutputKind.REPORT
    plugin_ref: str = "l6_phase4:memory_candidate"
    conflict_refs: tuple[str, ...] = field(default_factory=lambda: ("ref:l6_phase4_memory_conflict",))
    resolution_suggestion_ref: str = "summary:l6_phase4_memory_conflict_resolution_candidate"
    auto_resolution_allowed: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.conflict_refs, "MemoryConflictReport.conflict_refs", required=True)
        ensure_ref_text(self.resolution_suggestion_ref, "MemoryConflictReport.resolution_suggestion_ref")
        ensure_bool(self.auto_resolution_allowed, "MemoryConflictReport.auto_resolution_allowed")
        if self.auto_resolution_allowed:
            raise ValueError("memory conflict report cannot auto resolve")


@dataclass(frozen=True)
class MemoryDecayProjection(CognitiveOutputBase):
    output_ref: str = "projection:l6_phase4_memory_decay_projection"
    plugin_ref: str = "l6_phase4:forgetting_candidate"
    decay_score: float = 0.5
    retention_exception_hint_ref: str = "policy:l6_phase4_retention_exception_hint"
    direct_demotion_allowed: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        _score(self.decay_score, "MemoryDecayProjection.decay_score")
        ensure_ref_text(self.retention_exception_hint_ref, "MemoryDecayProjection.retention_exception_hint_ref")
        ensure_bool(self.direct_demotion_allowed, "MemoryDecayProjection.direct_demotion_allowed")
        if self.direct_demotion_allowed:
            raise ValueError("memory decay projection cannot directly demote memory")


@dataclass(frozen=True)
class MemoryPollutionRiskProjection(CognitiveOutputBase):
    output_ref: str = "projection:l6_phase4_memory_pollution_risk"
    plugin_ref: str = "l6_phase4:forgetting_candidate"
    pollution_risk_score: float = 0.0
    quarantine_suggestion_ref: str = "projection:l6_phase4_memory_quarantine_suggestion"
    direct_quarantine_allowed: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        _score(self.pollution_risk_score, "MemoryPollutionRiskProjection.pollution_risk_score")
        ensure_ref_text(self.quarantine_suggestion_ref, "MemoryPollutionRiskProjection.quarantine_suggestion_ref")
        ensure_bool(self.direct_quarantine_allowed, "MemoryPollutionRiskProjection.direct_quarantine_allowed")
        if self.direct_quarantine_allowed:
            raise ValueError("memory pollution risk projection cannot directly quarantine")


@dataclass(frozen=True)
class MemoryQuarantineSuggestion(CognitiveOutputBase):
    output_ref: str = "projection:l6_phase4_memory_quarantine_suggestion"
    output_kind: CognitiveOutputKind | str = CognitiveOutputKind.SUGGESTION
    plugin_ref: str = "l6_phase4:forgetting_candidate"
    quarantine_reason_ref: str = "ref:l6_phase4_memory_quarantine_reason"
    direct_quarantine_allowed: bool = False
    direct_removal: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_text(self.quarantine_reason_ref, "MemoryQuarantineSuggestion.quarantine_reason_ref")
        ensure_bool(self.direct_quarantine_allowed, "MemoryQuarantineSuggestion.direct_quarantine_allowed")
        ensure_bool(self.direct_removal, "MemoryQuarantineSuggestion.direct_removal")
        if self.direct_quarantine_allowed or self.direct_removal:
            raise ValueError("memory quarantine suggestion is not an action")


@dataclass(frozen=True)
class MemoryCompressionSuggestion(CognitiveOutputBase):
    output_ref: str = "projection:l6_phase4_memory_compression_suggestion"
    output_kind: CognitiveOutputKind | str = CognitiveOutputKind.SUGGESTION
    plugin_ref: str = "l6_phase4:memory_candidate"
    compression_summary_ref: str = "summary:l6_phase4_memory_compression_candidate"
    raw_memory_exposed: bool = False
    direct_rewrite_allowed: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_text(self.compression_summary_ref, "MemoryCompressionSuggestion.compression_summary_ref")
        ensure_bool(self.raw_memory_exposed, "MemoryCompressionSuggestion.raw_memory_exposed")
        ensure_bool(self.direct_rewrite_allowed, "MemoryCompressionSuggestion.direct_rewrite_allowed")
        if self.raw_memory_exposed or self.direct_rewrite_allowed:
            raise ValueError("memory compression suggestion cannot expose or rewrite memory")
