"""L6 phase4 resource-pressure and cost-aware review hints.

Phase4 only creates budget pressure projections, estimates, and degradation
suggestions.  It never charges budget, allocates quota, or decides permission.
"""

from __future__ import annotations

from dataclasses import dataclass

from tiangong_kernel.l6_plugins.common._common import ensure_bool, ensure_score, ensure_ref_text
from .common import CognitiveOutputKind
from .projection import CognitiveOutputBase


def _score(value: float, field_name: str) -> None:
    ensure_score(value, field_name)


@dataclass(frozen=True)
class ContextWindowPressureProjection(CognitiveOutputBase):
    output_ref: str = "projection:l6_phase4_context_window_pressure"
    plugin_ref: str = "l6_phase4:resource_budget_hint"
    pressure_score: float = 0.0
    compression_hint_ref: str = "summary:l6_phase4_context_compression_hint"
    direct_truncation_allowed: bool = False

    def __post_init__(self) -> None:
        super().__post_init__(); _score(self.pressure_score, "ContextWindowPressureProjection.pressure_score")
        ensure_ref_text(self.compression_hint_ref, "ContextWindowPressureProjection.compression_hint_ref")
        ensure_bool(self.direct_truncation_allowed, "ContextWindowPressureProjection.direct_truncation_allowed")
        if self.direct_truncation_allowed:
            raise ValueError("context window pressure cannot directly truncate context")


@dataclass(frozen=True)
class ToolLeasePressureProjection(CognitiveOutputBase):
    output_ref: str = "projection:l6_phase4_tool_lease_pressure"
    plugin_ref: str = "l6_phase4:resource_budget_hint"
    pressure_score: float = 0.0
    lease_review_ref: str = "l5:l6_phase4_tool_lease_review"
    direct_tool_stop_allowed: bool = False

    def __post_init__(self) -> None:
        super().__post_init__(); _score(self.pressure_score, "ToolLeasePressureProjection.pressure_score")
        ensure_ref_text(self.lease_review_ref, "ToolLeasePressureProjection.lease_review_ref")
        ensure_bool(self.direct_tool_stop_allowed, "ToolLeasePressureProjection.direct_tool_stop_allowed")
        if self.direct_tool_stop_allowed:
            raise ValueError("tool lease pressure cannot stop tools")


@dataclass(frozen=True)
class MemoryCandidateBatchLimitHint(CognitiveOutputBase):
    output_ref: str = "projection:l6_phase4_memory_candidate_batch_limit_hint"
    output_kind: CognitiveOutputKind | str = CognitiveOutputKind.HINT
    plugin_ref: str = "l6_phase4:resource_budget_hint"
    max_candidate_count_hint: int = 20
    is_hard_limit: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        if not isinstance(self.max_candidate_count_hint, int) or self.max_candidate_count_hint <= 0:
            raise ValueError("max_candidate_count_hint must be positive integer")
        ensure_bool(self.is_hard_limit, "MemoryCandidateBatchLimitHint.is_hard_limit")
        if self.is_hard_limit:
            raise ValueError("memory candidate batch limit hint cannot be hard limiter")


@dataclass(frozen=True)
class BudgetAwareDegradationSuggestion(CognitiveOutputBase):
    output_ref: str = "projection:l6_phase4_budget_aware_degradation_suggestion"
    output_kind: CognitiveOutputKind | str = CognitiveOutputKind.SUGGESTION
    plugin_ref: str = "l6_phase4:resource_budget_hint"
    expected_quality_impact: str = "summary:l6_phase4_quality_impact_low"
    governance_reason_ref: str = "l5:l6_phase4_budget_governance_reason"
    blocks_execution: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_text(self.expected_quality_impact, "BudgetAwareDegradationSuggestion.expected_quality_impact")
        ensure_ref_text(self.governance_reason_ref, "BudgetAwareDegradationSuggestion.governance_reason_ref")
        ensure_bool(self.blocks_execution, "BudgetAwareDegradationSuggestion.blocks_execution")
        if self.blocks_execution:
            raise ValueError("budget-aware degradation suggestion cannot block execution")


@dataclass(frozen=True)
class MemoryCompressionBudgetSuggestion(BudgetAwareDegradationSuggestion):
    output_ref: str = "projection:l6_phase4_memory_compression_budget_suggestion"
    plugin_ref: str = "l6_phase4:resource_budget_hint"


@dataclass(frozen=True)
class CandidateFactReviewBudgetHint(CognitiveOutputBase):
    output_ref: str = "projection:l6_phase4_candidate_fact_review_budget_hint"
    output_kind: CognitiveOutputKind | str = CognitiveOutputKind.HINT
    plugin_ref: str = "l6_phase4:resource_budget_hint"
    review_cost_score: float = 0.0
    skip_fact_review_allowed: bool = False

    def __post_init__(self) -> None:
        super().__post_init__(); _score(self.review_cost_score, "CandidateFactReviewBudgetHint.review_cost_score")
        ensure_bool(self.skip_fact_review_allowed, "CandidateFactReviewBudgetHint.skip_fact_review_allowed")
        if self.skip_fact_review_allowed:
            raise ValueError("budget hint cannot skip fact review")


@dataclass(frozen=True)
class WorldCandidateReviewPriorityHint(CognitiveOutputBase):
    output_ref: str = "projection:l6_phase4_world_candidate_review_priority_hint"
    output_kind: CognitiveOutputKind | str = CognitiveOutputKind.HINT
    plugin_ref: str = "l6_phase4:resource_budget_hint"
    review_priority_score: float = 0.5
    final_priority_decision: bool = False

    def __post_init__(self) -> None:
        super().__post_init__(); _score(self.review_priority_score, "WorldCandidateReviewPriorityHint.review_priority_score")
        ensure_bool(self.final_priority_decision, "WorldCandidateReviewPriorityHint.final_priority_decision")
        if self.final_priority_decision:
            raise ValueError("world candidate review priority hint is not final decision")


@dataclass(frozen=True)
class SelfReflectionCostEstimate(CognitiveOutputBase):
    output_ref: str = "projection:l6_phase4_self_reflection_cost_estimate"
    plugin_ref: str = "l6_phase4:resource_budget_hint"
    estimated_cost_score: float = 0.0
    auto_stop_allowed: bool = False

    def __post_init__(self) -> None:
        super().__post_init__(); _score(self.estimated_cost_score, "SelfReflectionCostEstimate.estimated_cost_score")
        ensure_bool(self.auto_stop_allowed, "SelfReflectionCostEstimate.auto_stop_allowed")
        if self.auto_stop_allowed:
            raise ValueError("cost estimate cannot auto stop self reflection")


@dataclass(frozen=True)
class LearningNeedCostEstimate(SelfReflectionCostEstimate):
    output_ref: str = "projection:l6_phase4_learning_need_cost_estimate"


@dataclass(frozen=True)
class RepairSuggestionCostClass(SelfReflectionCostEstimate):
    output_ref: str = "projection:l6_phase4_repair_suggestion_cost_class"


@dataclass(frozen=True)
class IterationCandidateBudgetPressureHint(SelfReflectionCostEstimate):
    output_ref: str = "projection:l6_phase4_iteration_candidate_budget_pressure_hint"


@dataclass(frozen=True)
class EvolutionCandidateCostRiskHint(SelfReflectionCostEstimate):
    output_ref: str = "projection:l6_phase4_evolution_candidate_cost_risk_hint"


@dataclass(frozen=True)
class RefusalReasonIntegrityCheck(CognitiveOutputBase):
    output_ref: str = "projection:l6_phase4_refusal_reason_integrity_check"
    plugin_ref: str = "l6_phase4:resource_budget_hint"
    governance_reason_ref: str = "l5:l6_phase4_governance_reason"
    affective_reason_only: bool = False
    refusal_allowed: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_text(self.governance_reason_ref, "RefusalReasonIntegrityCheck.governance_reason_ref")
        ensure_bool(self.affective_reason_only, "RefusalReasonIntegrityCheck.affective_reason_only")
        ensure_bool(self.refusal_allowed, "RefusalReasonIntegrityCheck.refusal_allowed")
        if self.affective_reason_only or not self.governance_reason_ref:
            raise ValueError("refusal reason integrity requires real governance reason")


@dataclass(frozen=True)
class ResourceBudgetReentryEnvelope(CognitiveOutputBase):
    output_ref: str = "l6:l6_phase4_resource_budget_reentry_envelope"
    output_kind: CognitiveOutputKind | str = CognitiveOutputKind.REENTRY_ENVELOPE
    plugin_ref: str = "l6_phase4:resource_budget_hint"
    l3_l5_review_required: bool = True
    charges_budget: bool = False
    allocates_quota: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_bool(self.l3_l5_review_required, "ResourceBudgetReentryEnvelope.l3_l5_review_required")
        ensure_bool(self.charges_budget, "ResourceBudgetReentryEnvelope.charges_budget")
        ensure_bool(self.allocates_quota, "ResourceBudgetReentryEnvelope.allocates_quota")
        if not self.l3_l5_review_required or self.charges_budget or self.allocates_quota:
            raise ValueError("resource budget reentry is review-only")
