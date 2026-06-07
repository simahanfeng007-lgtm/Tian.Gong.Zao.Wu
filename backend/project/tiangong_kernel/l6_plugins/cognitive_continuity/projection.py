"""L6 phase4 cognitive continuity projections and review candidates."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l6_plugins.common._common import (
    ensure_score,
    L6_COMMON_SCHEMA_VERSION,
    ensure_bool, ensure_score,
    ensure_no_live_or_sensitive_text,
    ensure_ref_items,
    ensure_ref_text,
    ensure_schema_version,
    stable_digest,
)
from .common import CognitiveOutputKind


def _score(value: float, field_name: str) -> None:
    ensure_score(value, field_name)


class PublicDisclosureClass(str, Enum):
    INTERNAL_REF_ONLY = "internal_ref_only"
    PUBLIC_MINIMAL = "public_minimal"
    REVIEW_ONLY = "review_only"


@dataclass(frozen=True)
class CognitiveOutputBase:
    output_ref: str = "projection:l6_phase4_output"
    output_kind: CognitiveOutputKind | str = CognitiveOutputKind.PROJECTION
    plugin_ref: str = "l6_phase4:plugin"
    evidence_refs: tuple[str, ...] = field(default_factory=lambda: ("evidence:l6_phase4_output",))
    trace_ref: str = "ref:l6_phase4_output_trace"
    audit_ref: str = "audit:l6_phase4_output"
    responsibility_chain_ref: str = "responsibility:l6_phase4_output"
    tamper_evidence_ref: str = "evidence:l6_phase4_output_tamper"
    summary: str = "summary:l6_phase4_output"
    disclosure_class: PublicDisclosureClass | str = PublicDisclosureClass.INTERNAL_REF_ONLY
    contains_raw_payload: bool = False
    contains_full_prompt: bool = False
    contains_real_path: bool = False
    contains_provider_locator: bool = False
    contains_credential_material: bool = False
    contains_complete_evidence_chain: bool = False
    contains_execution_plan: bool = False
    causes_side_effect: bool = False
    writes_l2_fact: bool = False
    writes_memory: bool = False
    removes_memory: bool = False
    grants_permission: bool = False
    dispatches_model: bool = False
    dispatches_tool: bool = False
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.output_ref, "CognitiveOutputBase.output_ref")
        object.__setattr__(self, "output_kind", CognitiveOutputKind(self.output_kind))
        ensure_ref_text(self.plugin_ref, "CognitiveOutputBase.plugin_ref")
        ensure_ref_items(self.evidence_refs, "CognitiveOutputBase.evidence_refs", required=True)
        for field_name in ("trace_ref", "audit_ref", "responsibility_chain_ref", "tamper_evidence_ref"):
            ensure_ref_text(getattr(self, field_name), f"CognitiveOutputBase.{field_name}")
        ensure_no_live_or_sensitive_text(self.summary, "CognitiveOutputBase.summary")
        object.__setattr__(self, "disclosure_class", PublicDisclosureClass(self.disclosure_class))
        for field_name in (
            "contains_raw_payload", "contains_full_prompt", "contains_real_path", "contains_provider_locator",
            "contains_credential_material", "contains_complete_evidence_chain", "contains_execution_plan", "causes_side_effect",
            "writes_l2_fact", "writes_memory", "removes_memory", "grants_permission", "dispatches_model", "dispatches_tool",
        ):
            ensure_bool(getattr(self, field_name), f"CognitiveOutputBase.{field_name}")
        if any(
            (
                self.contains_raw_payload,
                self.contains_full_prompt,
                self.contains_real_path,
                self.contains_provider_locator,
                self.contains_credential_material,
                self.contains_complete_evidence_chain,
                self.contains_execution_plan,
                self.causes_side_effect,
                self.writes_l2_fact,
                self.writes_memory,
                self.removes_memory,
                self.grants_permission,
                self.dispatches_model,
                self.dispatches_tool,
            )
        ):
            raise ValueError("Phase4 outputs must be redacted inert review objects")
        ensure_schema_version(self.schema_version)

    @property
    def digest(self) -> str:
        return stable_digest(self)


@dataclass(frozen=True)
class ContextContinuityProjection(CognitiveOutputBase):
    output_ref: str = "projection:l6_phase4_context_continuity"
    plugin_ref: str = "l6_phase4:context_continuity"
    continuity_score: float = 0.5
    reentry_required: bool = True
    is_prompt_injection: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        _score(self.continuity_score, "ContextContinuityProjection.continuity_score")
        ensure_bool(self.reentry_required, "ContextContinuityProjection.reentry_required")
        ensure_bool(self.is_prompt_injection, "ContextContinuityProjection.is_prompt_injection")
        if not self.reentry_required or self.is_prompt_injection:
            raise ValueError("context continuity projection must be review-mediated and not prompt injection")


@dataclass(frozen=True)
class ContextSafetyReviewRequest(CognitiveOutputBase):
    output_ref: str = "projection:l6_phase4_context_safety_review_request"
    output_kind: CognitiveOutputKind | str = CognitiveOutputKind.REVIEW_REQUEST
    plugin_ref: str = "l6_phase4:context_continuity"
    review_target_ref: str = "context:l6_phase4_candidate_context"
    l5_context_policy_required: bool = True

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_text(self.review_target_ref, "ContextSafetyReviewRequest.review_target_ref")
        ensure_bool(self.l5_context_policy_required, "ContextSafetyReviewRequest.l5_context_policy_required")
        if not self.l5_context_policy_required:
            raise ValueError("context safety review must require L5 context policy")


@dataclass(frozen=True)
class MemoryRecallReentryCandidate(CognitiveOutputBase):
    output_ref: str = "projection:l6_phase4_memory_recall_candidate"
    output_kind: CognitiveOutputKind | str = CognitiveOutputKind.CANDIDATE
    plugin_ref: str = "l6_phase4:memory_candidate"
    recall_priority_score: float = 0.5
    force_recall: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        _score(self.recall_priority_score, "MemoryRecallReentryCandidate.recall_priority_score")
        ensure_bool(self.force_recall, "MemoryRecallReentryCandidate.force_recall")
        if self.force_recall:
            raise ValueError("memory recall candidate cannot force recall")


@dataclass(frozen=True)
class MemoryPromotionReviewCandidate(CognitiveOutputBase):
    output_ref: str = "projection:l6_phase4_memory_promotion_review_candidate"
    output_kind: CognitiveOutputKind | str = CognitiveOutputKind.CANDIDATE
    plugin_ref: str = "l6_phase4:memory_candidate"
    promotion_score: float = 0.5
    memory_update_proposal: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        _score(self.promotion_score, "MemoryPromotionReviewCandidate.promotion_score")
        ensure_bool(self.memory_update_proposal, "MemoryPromotionReviewCandidate.memory_update_proposal")
        if self.memory_update_proposal:
            raise ValueError("memory promotion review candidate is not a memory update proposal")


@dataclass(frozen=True)
class MemoryProposalReviewRequest(CognitiveOutputBase):
    output_ref: str = "projection:l6_phase4_memory_proposal_review_request"
    output_kind: CognitiveOutputKind | str = CognitiveOutputKind.REVIEW_REQUEST
    plugin_ref: str = "l6_phase4:memory_candidate"
    proposal_ref: str = "projection:l6_phase4_memory_promotion_review_candidate"
    l3_l5_review_required: bool = True
    memory_system_review_required: bool = True

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_text(self.proposal_ref, "MemoryProposalReviewRequest.proposal_ref")
        ensure_bool(self.l3_l5_review_required, "MemoryProposalReviewRequest.l3_l5_review_required")
        ensure_bool(self.memory_system_review_required, "MemoryProposalReviewRequest.memory_system_review_required")
        if not self.l3_l5_review_required or not self.memory_system_review_required:
            raise ValueError("memory proposal must go through review")


@dataclass(frozen=True)
class ForgettingReviewCandidate(CognitiveOutputBase):
    output_ref: str = "projection:l6_phase4_forgetting_review_candidate"
    output_kind: CognitiveOutputKind | str = CognitiveOutputKind.CANDIDATE
    plugin_ref: str = "l6_phase4:forgetting_candidate"
    forgetting_score: float = 0.5
    retention_exception_required: bool = False
    direct_removal: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        _score(self.forgetting_score, "ForgettingReviewCandidate.forgetting_score")
        ensure_bool(self.retention_exception_required, "ForgettingReviewCandidate.retention_exception_required")
        ensure_bool(self.direct_removal, "ForgettingReviewCandidate.direct_removal")
        if self.direct_removal:
            raise ValueError("forgetting review candidate cannot remove memory")


@dataclass(frozen=True)
class TombstoneProposal(CognitiveOutputBase):
    output_ref: str = "projection:l6_phase4_tombstone_proposal"
    output_kind: CognitiveOutputKind | str = CognitiveOutputKind.CANDIDATE
    plugin_ref: str = "l6_phase4:forgetting_candidate"
    tombstone_only: bool = True
    direct_removal: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_bool(self.tombstone_only, "TombstoneProposal.tombstone_only")
        ensure_bool(self.direct_removal, "TombstoneProposal.direct_removal")
        if not self.tombstone_only or self.direct_removal:
            raise ValueError("tombstone proposal must remain proposal-only")


@dataclass(frozen=True)
class ActiveRecallSuppressionProposal(CognitiveOutputBase):
    output_ref: str = "projection:l6_phase4_active_recall_suppression"
    output_kind: CognitiveOutputKind | str = CognitiveOutputKind.CANDIDATE
    plugin_ref: str = "l6_phase4:forgetting_candidate"
    suppression_only: bool = True
    direct_memory_change: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_bool(self.suppression_only, "ActiveRecallSuppressionProposal.suppression_only")
        ensure_bool(self.direct_memory_change, "ActiveRecallSuppressionProposal.direct_memory_change")
        if not self.suppression_only or self.direct_memory_change:
            raise ValueError("active recall suppression is a review proposal only")


@dataclass(frozen=True)
class ForgettingProposalReviewRequest(CognitiveOutputBase):
    output_ref: str = "projection:l6_phase4_forgetting_proposal_review_request"
    output_kind: CognitiveOutputKind | str = CognitiveOutputKind.REVIEW_REQUEST
    plugin_ref: str = "l6_phase4:forgetting_candidate"
    proposal_refs: tuple[str, ...] = field(default_factory=lambda: ("projection:l6_phase4_forgetting_review_candidate",))
    forgetting_system_review_required: bool = True
    deletion_review_required: bool = True

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.proposal_refs, "ForgettingProposalReviewRequest.proposal_refs", required=True)
        ensure_bool(self.forgetting_system_review_required, "ForgettingProposalReviewRequest.forgetting_system_review_required")
        ensure_bool(self.deletion_review_required, "ForgettingProposalReviewRequest.deletion_review_required")
        if not self.forgetting_system_review_required or not self.deletion_review_required:
            raise ValueError("forgetting proposal must require forgetting/deletion review")


@dataclass(frozen=True)
class BeliefWorldReviewProjection(CognitiveOutputBase):
    output_ref: str = "projection:l6_phase4_belief_world_review"
    plugin_ref: str = "l6_phase4:belief_world_review"
    belief_confidence_delta: float = 0.0
    world_candidate_strength: float = 0.5
    canonical_state: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        _score(abs(self.belief_confidence_delta), "BeliefWorldReviewProjection.belief_confidence_delta_abs")
        _score(self.world_candidate_strength, "BeliefWorldReviewProjection.world_candidate_strength")
        ensure_bool(self.canonical_state, "BeliefWorldReviewProjection.canonical_state")
        if self.canonical_state:
            raise ValueError("belief/world review projection cannot be canonical state")


@dataclass(frozen=True)
class CandidateFactReviewRequest(CognitiveOutputBase):
    output_ref: str = "projection:l6_phase4_candidate_fact_review_request"
    output_kind: CognitiveOutputKind | str = CognitiveOutputKind.REVIEW_REQUEST
    plugin_ref: str = "l6_phase4:belief_world_review"
    candidate_fact_ref: str = "projection:l6_phase4_candidate_fact"
    writes_l2_fact: bool = False
    l2_review_required: bool = True

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_text(self.candidate_fact_ref, "CandidateFactReviewRequest.candidate_fact_ref")
        ensure_bool(self.l2_review_required, "CandidateFactReviewRequest.l2_review_required")
        if self.writes_l2_fact or not self.l2_review_required:
            raise ValueError("candidate fact review request cannot write L2 directly")


@dataclass(frozen=True)
class SelfReflectionLearningCandidate(CognitiveOutputBase):
    output_ref: str = "projection:l6_phase4_self_reflection_learning_candidate"
    output_kind: CognitiveOutputKind | str = CognitiveOutputKind.CANDIDATE
    plugin_ref: str = "l6_phase4:self_reflection_learning"
    learning_need_score: float = 0.5
    self_healing_candidate: bool = True
    auto_repair: bool = False
    auto_migration: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        _score(self.learning_need_score, "SelfReflectionLearningCandidate.learning_need_score")
        ensure_bool(self.self_healing_candidate, "SelfReflectionLearningCandidate.self_healing_candidate")
        ensure_bool(self.auto_repair, "SelfReflectionLearningCandidate.auto_repair")
        ensure_bool(self.auto_migration, "SelfReflectionLearningCandidate.auto_migration")
        if self.auto_repair or self.auto_migration:
            raise ValueError("self-reflection learning candidate cannot auto repair or migrate")


@dataclass(frozen=True)
class ProductSpecSeedCandidate(CognitiveOutputBase):
    output_ref: str = "projection:l6_phase4_product_spec_seed_candidate"
    output_kind: CognitiveOutputKind | str = CognitiveOutputKind.CANDIDATE
    plugin_ref: str = "l6_phase4:product_bridge_seed"
    seed_quality_score: float = 0.5
    intent_summary_ref: str = "summary:l6_phase4_product_intent"
    source_context_refs: tuple[str, ...] = field(default_factory=lambda: ("context:l6_phase4_product_source_context",))
    requirement_hint_refs: tuple[str, ...] = field(default_factory=lambda: ("requirement:l6_phase4_product_requirement_hint",))
    artifact_type_hint_ref: str = "product:l6_phase4_artifact_type_hint"
    privacy_review_ref: str = "review:l6_phase4_product_privacy_review"
    readiness_hint_ref: str = "hint:l6_phase4_product_readiness"
    is_product_spec: bool = False
    creates_product_spec: bool = False
    build_action_allowed: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        _score(self.seed_quality_score, "ProductSpecSeedCandidate.seed_quality_score")
        ensure_ref_text(self.intent_summary_ref, "ProductSpecSeedCandidate.intent_summary_ref")
        ensure_ref_items(self.source_context_refs, "ProductSpecSeedCandidate.source_context_refs", required=True)
        ensure_ref_items(self.requirement_hint_refs, "ProductSpecSeedCandidate.requirement_hint_refs", required=True)
        for field_name in ("artifact_type_hint_ref", "privacy_review_ref", "readiness_hint_ref"):
            ensure_ref_text(getattr(self, field_name), f"ProductSpecSeedCandidate.{field_name}")
        ensure_bool(self.is_product_spec, "ProductSpecSeedCandidate.is_product_spec")
        ensure_bool(self.creates_product_spec, "ProductSpecSeedCandidate.creates_product_spec")
        ensure_bool(self.build_action_allowed, "ProductSpecSeedCandidate.build_action_allowed")
        if self.is_product_spec or self.creates_product_spec or self.build_action_allowed:
            raise ValueError("product spec seed is not a product spec and cannot build")


@dataclass(frozen=True)
class CognitivePublicProjection(CognitiveOutputBase):
    output_ref: str = "public:l6_phase4_cognitive_continuity"
    output_kind: CognitiveOutputKind | str = CognitiveOutputKind.PROJECTION
    plugin_ref: str = "l6_phase4:cognitive_reentry_fusion"
    disclosure_class: PublicDisclosureClass | str = PublicDisclosureClass.PUBLIC_MINIMAL
    health_summary_ref: str = "summary:l6_phase4_health"
    risk_level_ref: str = "summary:l6_phase4_risk_low"
    evidence_count: int = 1
    redaction_flags: tuple[str, ...] = field(default_factory=lambda: (
        "redact:full_affective_profile", "redact:full_private_memory", "redact:full_prompt", "redact:provider_locator", "redact:complete_execution_plan"
    ))

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_text(self.health_summary_ref, "CognitivePublicProjection.health_summary_ref")
        ensure_ref_text(self.risk_level_ref, "CognitivePublicProjection.risk_level_ref")
        if not isinstance(self.evidence_count, int) or self.evidence_count < 0:
            raise ValueError("CognitivePublicProjection.evidence_count must be non-negative integer")
        ensure_ref_items(self.redaction_flags, "CognitivePublicProjection.redaction_flags", required=True)
