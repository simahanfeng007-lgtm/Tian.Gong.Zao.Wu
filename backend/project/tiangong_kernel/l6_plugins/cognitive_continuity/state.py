"""L6 phase4 cognitive continuity state envelopes.

Phase4 states are review-oriented summaries. They are not L2 facts, not memory
records, not deletion commands, and not execution plans.
"""

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
from .common import L6_PHASE4, CognitiveContinuityPluginKind


def _score(value: float, field_name: str) -> None:
    ensure_score(value, field_name)


class CognitiveContinuityStateDomain(str, Enum):
    CONTEXT_CONTINUITY = "context_continuity"
    MEMORY_CANDIDATE = "memory_candidate"
    FORGETTING_CANDIDATE = "forgetting_candidate"
    BELIEF_WORLD_REVIEW = "belief_world_review"
    AFFECTIVE_MODULATION = "affective_modulation"
    SELF_REFLECTION_LEARNING = "self_reflection_learning"
    REENTRY_FUSION = "reentry_fusion"
    PRODUCT_BRIDGE_SEED = "product_bridge_seed"


@dataclass(frozen=True)
class CognitiveContinuityStateEnvelope:
    state_ref: str = "state:l6_phase4_cognitive_continuity"
    phase: str = L6_PHASE4
    domain: CognitiveContinuityStateDomain | str = CognitiveContinuityStateDomain.CONTEXT_CONTINUITY
    plugin_ref: str = "l6_phase4:context_continuity"
    source_refs: tuple[str, ...] = field(default_factory=lambda: ("summary:l6_phase4_source",))
    evidence_refs: tuple[str, ...] = field(default_factory=lambda: ("evidence:l6_phase4_state",))
    trace_ref: str = "ref:l6_phase4_state_trace"
    audit_ref: str = "audit:l6_phase4_state"
    responsibility_chain_ref: str = "responsibility:l6_phase4_state"
    confidence_score: float = 0.5
    uncertainty_score: float = 0.5
    risk_score: float = 0.0
    freshness_score: float = 0.5
    digest_summary: str = "summary:l6_phase4_state"
    is_l2_fact: bool = False
    is_execution_plan: bool = False
    is_memory_record: bool = False
    is_removal_order: bool = False
    contains_raw_payload: bool = False
    contains_full_private_profile: bool = False
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.state_ref, "CognitiveContinuityStateEnvelope.state_ref")
        if self.phase != L6_PHASE4:
            raise ValueError("CognitiveContinuityStateEnvelope.phase must be L6 phase4")
        object.__setattr__(self, "domain", CognitiveContinuityStateDomain(self.domain))
        ensure_ref_text(self.plugin_ref, "CognitiveContinuityStateEnvelope.plugin_ref")
        ensure_ref_items(self.source_refs, "CognitiveContinuityStateEnvelope.source_refs", required=True)
        ensure_ref_items(self.evidence_refs, "CognitiveContinuityStateEnvelope.evidence_refs", required=True)
        for field_name in ("trace_ref", "audit_ref", "responsibility_chain_ref"):
            ensure_ref_text(getattr(self, field_name), f"CognitiveContinuityStateEnvelope.{field_name}")
        for field_name in ("confidence_score", "uncertainty_score", "risk_score", "freshness_score"):
            _score(getattr(self, field_name), f"CognitiveContinuityStateEnvelope.{field_name}")
        ensure_no_live_or_sensitive_text(self.digest_summary, "CognitiveContinuityStateEnvelope.digest_summary")
        for field_name in (
            "is_l2_fact", "is_execution_plan", "is_memory_record", "is_removal_order", "contains_raw_payload", "contains_full_private_profile",
        ):
            ensure_bool(getattr(self, field_name), f"CognitiveContinuityStateEnvelope.{field_name}")
        if any((self.is_l2_fact, self.is_execution_plan, self.is_memory_record, self.is_removal_order, self.contains_raw_payload, self.contains_full_private_profile)):
            raise ValueError("Phase4 cognitive state must remain ref-only candidate state")
        ensure_schema_version(self.schema_version)

    @property
    def digest(self) -> str:
        return stable_digest(self)


@dataclass(frozen=True)
class ContextContinuityState(CognitiveContinuityStateEnvelope):
    state_ref: str = "state:l6_phase4_context_continuity"
    domain: CognitiveContinuityStateDomain | str = CognitiveContinuityStateDomain.CONTEXT_CONTINUITY
    plugin_ref: str = "l6_phase4:context_continuity"
    continuity_score: float = 0.5
    gap_score: float = 0.0

    def __post_init__(self) -> None:
        super().__post_init__()
        _score(self.continuity_score, "ContextContinuityState.continuity_score")
        _score(self.gap_score, "ContextContinuityState.gap_score")


@dataclass(frozen=True)
class MemoryCandidateContinuityState(CognitiveContinuityStateEnvelope):
    state_ref: str = "state:l6_phase4_memory_candidate"
    domain: CognitiveContinuityStateDomain | str = CognitiveContinuityStateDomain.MEMORY_CANDIDATE
    plugin_ref: str = "l6_phase4:memory_candidate"
    promotion_readiness_score: float = 0.0
    privacy_risk_score: float = 0.0

    def __post_init__(self) -> None:
        super().__post_init__()
        _score(self.promotion_readiness_score, "MemoryCandidateContinuityState.promotion_readiness_score")
        _score(self.privacy_risk_score, "MemoryCandidateContinuityState.privacy_risk_score")


@dataclass(frozen=True)
class ForgettingCandidateContinuityState(CognitiveContinuityStateEnvelope):
    state_ref: str = "state:l6_phase4_forgetting_candidate"
    domain: CognitiveContinuityStateDomain | str = CognitiveContinuityStateDomain.FORGETTING_CANDIDATE
    plugin_ref: str = "l6_phase4:forgetting_candidate"
    user_forget_signal_score: float = 0.0
    protected_retention_score: float = 0.0

    def __post_init__(self) -> None:
        super().__post_init__()
        _score(self.user_forget_signal_score, "ForgettingCandidateContinuityState.user_forget_signal_score")
        _score(self.protected_retention_score, "ForgettingCandidateContinuityState.protected_retention_score")
        if self.protected_retention_score >= 0.9 and self.is_removal_order:
            raise ValueError("protected retention cannot become removal order")


@dataclass(frozen=True)
class BeliefWorldReviewState(CognitiveContinuityStateEnvelope):
    state_ref: str = "state:l6_phase4_belief_world_review"
    domain: CognitiveContinuityStateDomain | str = CognitiveContinuityStateDomain.BELIEF_WORLD_REVIEW
    plugin_ref: str = "l6_phase4:belief_world_review"
    candidate_fact_strength: float = 0.5
    affective_contamination_score: float = 0.0

    def __post_init__(self) -> None:
        super().__post_init__()
        _score(self.candidate_fact_strength, "BeliefWorldReviewState.candidate_fact_strength")
        _score(self.affective_contamination_score, "BeliefWorldReviewState.affective_contamination_score")


@dataclass(frozen=True)
class AffectiveModulationState(CognitiveContinuityStateEnvelope):
    state_ref: str = "state:l6_phase4_affective_modulation"
    domain: CognitiveContinuityStateDomain | str = CognitiveContinuityStateDomain.AFFECTIVE_MODULATION
    plugin_ref: str = "l6_phase4:affective_reentry"
    modulation_only: bool = True
    fatigue_score: float = 0.0
    resource_pressure_score: float = 0.0
    pollution_score: float = 0.0

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_bool(self.modulation_only, "AffectiveModulationState.modulation_only")
        if not self.modulation_only:
            raise ValueError("Affective modulation state must stay modulation-only")
        for field_name in ("fatigue_score", "resource_pressure_score", "pollution_score"):
            _score(getattr(self, field_name), f"AffectiveModulationState.{field_name}")


@dataclass(frozen=True)
class SelfReflectionLearningState(CognitiveContinuityStateEnvelope):
    state_ref: str = "state:l6_phase4_self_reflection_learning"
    domain: CognitiveContinuityStateDomain | str = CognitiveContinuityStateDomain.SELF_REFLECTION_LEARNING
    plugin_ref: str = "l6_phase4:self_reflection_learning"
    learning_need_score: float = 0.0
    repair_candidate_score: float = 0.0
    auto_repair_allowed: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        _score(self.learning_need_score, "SelfReflectionLearningState.learning_need_score")
        _score(self.repair_candidate_score, "SelfReflectionLearningState.repair_candidate_score")
        ensure_bool(self.auto_repair_allowed, "SelfReflectionLearningState.auto_repair_allowed")
        if self.auto_repair_allowed:
            raise ValueError("Phase4 learning state cannot auto repair")


@dataclass(frozen=True)
class CognitiveReentryFusionState(CognitiveContinuityStateEnvelope):
    state_ref: str = "state:l6_phase4_reentry_fusion"
    domain: CognitiveContinuityStateDomain | str = CognitiveContinuityStateDomain.REENTRY_FUSION
    plugin_ref: str = "l6_phase4:cognitive_reentry_fusion"
    conflict_score: float = 0.0
    l3_l5_review_required: bool = True

    def __post_init__(self) -> None:
        super().__post_init__()
        _score(self.conflict_score, "CognitiveReentryFusionState.conflict_score")
        ensure_bool(self.l3_l5_review_required, "CognitiveReentryFusionState.l3_l5_review_required")
        if not self.l3_l5_review_required:
            raise ValueError("Cognitive reentry fusion must require L3/L5 review")


@dataclass(frozen=True)
class ProductBridgeSeedState(CognitiveContinuityStateEnvelope):
    state_ref: str = "state:l6_phase4_product_bridge_seed"
    domain: CognitiveContinuityStateDomain | str = CognitiveContinuityStateDomain.PRODUCT_BRIDGE_SEED
    plugin_ref: str = "l6_phase4:product_bridge_seed"
    product_spec_created: bool = False
    build_action_allowed: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_bool(self.product_spec_created, "ProductBridgeSeedState.product_spec_created")
        ensure_bool(self.build_action_allowed, "ProductBridgeSeedState.build_action_allowed")
        if self.product_spec_created or self.build_action_allowed:
            raise ValueError("Phase4 product bridge can only hold seed candidates")
