"""Risk assessment declarations for L6 phase5 governance-control."""

from __future__ import annotations

from dataclasses import dataclass, field

from .common import GovernanceArtifactBase, RiskTier, ensure_bool, ensure_ref_items, ensure_ref_text, ensure_score, stable_digest


@dataclass(frozen=True)
class RiskProjection(GovernanceArtifactBase):
    object_ref: str = "projection:l6_phase5_risk"
    risk_level: RiskTier | str = RiskTier.A2
    risk_score: float = 0.35
    is_final_decision: bool = False
    denies_execution: bool = False
    blocks_by_default: bool = False
    requires_hard_boundary_review: bool = False
    continuation_preferred_when_safe: bool = True

    def __post_init__(self) -> None:
        super().__post_init__()
        object.__setattr__(self, "risk_level", RiskTier(self.risk_level))
        ensure_score(self.risk_score, "RiskProjection.risk_score")
        for field_name in ("is_final_decision", "denies_execution", "blocks_by_default", "requires_hard_boundary_review", "continuation_preferred_when_safe"):
            ensure_bool(getattr(self, field_name), f"RiskProjection.{field_name}")
        if self.is_final_decision or self.denies_execution or self.blocks_by_default:
            raise ValueError("RiskProjection is not a final decision, denial, or default blocker")
        if self.risk_level is RiskTier.A5 and not self.requires_hard_boundary_review:
            raise ValueError("A5 risk must request hard-boundary review")
        if self.risk_level is not RiskTier.A5 and self.requires_hard_boundary_review and self.risk_score < 0.9:
            raise ValueError("Hard-boundary review must be reserved for high-confidence hard boundaries")
        if not self.continuation_preferred_when_safe:
            raise ValueError("Phase5 risk projection must prefer continuation when safe")


@dataclass(frozen=True)
class RiskLevelHint(GovernanceArtifactBase):
    object_ref: str = "hint:l6_phase5_risk_level"
    risk_level: RiskTier | str = RiskTier.A2
    risk_score: float = 0.30
    score_is_decision: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        object.__setattr__(self, "risk_level", RiskTier(self.risk_level))
        ensure_score(self.risk_score, "RiskLevelHint.risk_score")
        ensure_bool(self.score_is_decision, "RiskLevelHint.score_is_decision")
        if self.score_is_decision:
            raise ValueError("Risk score cannot be decision")


@dataclass(frozen=True)
class A5HardBoundaryHint(GovernanceArtifactBase):
    object_ref: str = "hint:l6_phase5_a5_hard_boundary"
    risk_level: RiskTier | str = RiskTier.A5
    hard_boundary_reason_refs: tuple[str, ...] = field(default_factory=lambda: ("policy:a5_hard_boundary",))
    final_decision_allowed: bool = False
    l5_review_required: bool = True

    def __post_init__(self) -> None:
        super().__post_init__()
        object.__setattr__(self, "risk_level", RiskTier(self.risk_level))
        ensure_ref_items(self.hard_boundary_reason_refs, "A5HardBoundaryHint.hard_boundary_reason_refs", required=True)
        ensure_bool(self.final_decision_allowed, "A5HardBoundaryHint.final_decision_allowed")
        ensure_bool(self.l5_review_required, "A5HardBoundaryHint.l5_review_required")
        if self.risk_level is not RiskTier.A5:
            raise ValueError("A5HardBoundaryHint must use A5 level")
        if self.final_decision_allowed or not self.l5_review_required:
            raise ValueError("A5 hint must still be reviewed by L5 and cannot decide")


@dataclass(frozen=True)
class RiskAccumulationProjection(GovernanceArtifactBase):
    object_ref: str = "projection:l6_phase5_risk_accumulation"
    accumulated_risk_score: float = 0.42
    risk_segment_refs: tuple[str, ...] = field(default_factory=lambda: ("ref:l6_phase5_risk_segment",))
    stop_by_default: bool = False
    summarize_not_interrupt: bool = True

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_score(self.accumulated_risk_score, "RiskAccumulationProjection.accumulated_risk_score")
        ensure_ref_items(self.risk_segment_refs, "RiskAccumulationProjection.risk_segment_refs", required=True)
        ensure_bool(self.stop_by_default, "RiskAccumulationProjection.stop_by_default")
        ensure_bool(self.summarize_not_interrupt, "RiskAccumulationProjection.summarize_not_interrupt")
        if self.stop_by_default or not self.summarize_not_interrupt:
            raise ValueError("Long-chain risk accumulation must summarize rather than interrupt by default")


@dataclass(frozen=True)
class GovernanceRiskSummary(GovernanceArtifactBase):
    object_ref: str = "summary:l6_phase5_governance_risk"
    risk_projection_refs: tuple[str, ...] = field(default_factory=lambda: ("projection:l6_phase5_risk",))
    continuation_hint_ref: str = "hint:l6_phase5_continuation"
    final_risk_decision: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.risk_projection_refs, "GovernanceRiskSummary.risk_projection_refs", required=True)
        ensure_ref_text(self.continuation_hint_ref, "GovernanceRiskSummary.continuation_hint_ref")
        ensure_bool(self.final_risk_decision, "GovernanceRiskSummary.final_risk_decision")
        if self.final_risk_decision:
            raise ValueError("GovernanceRiskSummary cannot be final risk decision")


@dataclass(frozen=True)
class ReversibilityRiskHint(GovernanceArtifactBase):
    object_ref: str = "hint:l6_phase5_reversibility_risk"
    reversible: bool = True
    continuation_preferred: bool = True
    requires_hard_boundary_review: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        for field_name in ("reversible", "continuation_preferred", "requires_hard_boundary_review"):
            ensure_bool(getattr(self, field_name), f"ReversibilityRiskHint.{field_name}")
        if self.reversible and not self.continuation_preferred:
            raise ValueError("Reversible candidates should continue when other hard boundaries are absent")


@dataclass(frozen=True)
class SideEffectRiskHint(GovernanceArtifactBase):
    object_ref: str = "hint:l6_phase5_side_effect_risk"
    irreversible_side_effect_possible: bool = False
    hard_boundary_review_required: bool = False
    direct_execution_allowed: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        for field_name in ("irreversible_side_effect_possible", "hard_boundary_review_required", "direct_execution_allowed"):
            ensure_bool(getattr(self, field_name), f"SideEffectRiskHint.{field_name}")
        if self.direct_execution_allowed:
            raise ValueError("SideEffectRiskHint cannot allow direct execution")
        if self.irreversible_side_effect_possible and not self.hard_boundary_review_required:
            raise ValueError("Irreversible side-effect possibility requires hard-boundary review")


@dataclass(frozen=True)
class RiskAssessmentPluginPlan(GovernanceArtifactBase):
    object_ref: str = "l6_phase5:risk_assessment_plugin_plan"
    output_refs: tuple[str, ...] = field(default_factory=lambda: ("projection:l6_phase5_risk", "request:l6_phase5_governance_review"))
    direct_allow_or_deny: bool = False
    blocks_low_risk: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.output_refs, "RiskAssessmentPluginPlan.output_refs", required=True)
        ensure_bool(self.direct_allow_or_deny, "RiskAssessmentPluginPlan.direct_allow_or_deny")
        ensure_bool(self.blocks_low_risk, "RiskAssessmentPluginPlan.blocks_low_risk")
        if self.direct_allow_or_deny or self.blocks_low_risk:
            raise ValueError("RiskAssessmentPluginPlan must not allow/deny or block low-risk flow")
