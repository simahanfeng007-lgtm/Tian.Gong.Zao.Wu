"""Budget and resource pressure declarations for L6 phase5."""

from __future__ import annotations

from dataclasses import dataclass, field

from .common import GovernanceArtifactBase, ensure_bool, ensure_no_live_or_sensitive_text, ensure_ref_items, ensure_ref_text, ensure_score


@dataclass(frozen=True)
class BudgetRequirement(GovernanceArtifactBase):
    object_ref: str = "budget:l6_phase5_requirement"
    requirement_only: bool = True
    allocation_made: bool = False
    charge_made: bool = False
    l5_budget_review_required: bool = True
    run_budget_scope_ref: str = "run:l6_phase5_budget_scope"
    goal_budget_scope_ref: str = "goal:l6_phase5_budget_scope"
    actor_budget_scope_ref: str = "actor:l6_phase5_budget_scope"
    budget_owner_ref: str = "budget:l6_phase5_budget_owner"
    high_permission_budget_bypass: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        for field_name in ("run_budget_scope_ref", "goal_budget_scope_ref", "actor_budget_scope_ref", "budget_owner_ref"):
            ensure_ref_text(getattr(self, field_name), f"BudgetRequirement.{field_name}")
        for field_name in ("requirement_only", "allocation_made", "charge_made", "l5_budget_review_required", "high_permission_budget_bypass"):
            ensure_bool(getattr(self, field_name), f"BudgetRequirement.{field_name}")
        if not self.requirement_only or self.allocation_made or self.charge_made or not self.l5_budget_review_required or self.high_permission_budget_bypass:
            raise ValueError("BudgetRequirement is not allocation, budget charge, or high-permission bypass")


@dataclass(frozen=True)
class BudgetPressureProjection(GovernanceArtifactBase):
    object_ref: str = "projection:l6_phase5_budget_pressure"
    pressure_score: float = 0.5
    budget_exhausted: bool = False
    governance_reason_ref: str = "policy:l6_phase5_budget_review"
    stops_task_by_default: bool = False
    degradation_preferred: bool = True
    run_budget_scope_ref: str = "run:l6_phase5_budget_pressure_scope"
    goal_budget_scope_ref: str = "goal:l6_phase5_budget_pressure_scope"
    actor_budget_scope_ref: str = "actor:l6_phase5_budget_pressure_scope"
    budget_owner_ref: str = "budget:l6_phase5_budget_pressure_owner"
    quota_reservation_made: bool = False
    live_budget_decrement_made: bool = False
    evidence_refs: tuple[str, ...] = field(default_factory=lambda: ("evidence:l6_phase5_budget_pressure",))

    def __post_init__(self) -> None:
        super().__post_init__()
        for field_name in ("run_budget_scope_ref", "goal_budget_scope_ref", "actor_budget_scope_ref", "budget_owner_ref"):
            ensure_ref_text(getattr(self, field_name), f"BudgetPressureProjection.{field_name}")
        ensure_ref_items(self.evidence_refs, "BudgetPressureProjection.evidence_refs", required=True)
        ensure_score(self.pressure_score, "BudgetPressureProjection.pressure_score")
        ensure_bool(self.budget_exhausted, "BudgetPressureProjection.budget_exhausted")
        ensure_ref_text(self.governance_reason_ref, "BudgetPressureProjection.governance_reason_ref")
        ensure_bool(self.stops_task_by_default, "BudgetPressureProjection.stops_task_by_default")
        ensure_bool(self.degradation_preferred, "BudgetPressureProjection.degradation_preferred")
        ensure_bool(self.quota_reservation_made, "BudgetPressureProjection.quota_reservation_made")
        ensure_bool(self.live_budget_decrement_made, "BudgetPressureProjection.live_budget_decrement_made")
        if self.stops_task_by_default or not self.degradation_preferred or self.quota_reservation_made or self.live_budget_decrement_made:
            raise ValueError("Budget pressure should degrade/review only and never reserve quota or decrement budget")
        if self.budget_exhausted and not self.governance_reason_ref:
            raise ValueError("Budget exhaustion must bind governance reason")


@dataclass(frozen=True)
class ResourcePressureProjection(GovernanceArtifactBase):
    object_ref: str = "projection:l6_phase5_resource_pressure"
    resource_pressure_score: float = 0.45
    fatigue_reason: bool = False
    real_resource_reason_ref: str = "budget:l6_phase5_resource_pressure"
    continue_with_low_energy_mode: bool = True
    run_budget_scope_ref: str = "run:l6_phase5_resource_scope"
    goal_budget_scope_ref: str = "goal:l6_phase5_resource_scope"
    actor_budget_scope_ref: str = "actor:l6_phase5_resource_scope"
    budget_owner_ref: str = "budget:l6_phase5_resource_owner"
    resource_allocation_made: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        for field_name in ("run_budget_scope_ref", "goal_budget_scope_ref", "actor_budget_scope_ref", "budget_owner_ref"):
            ensure_ref_text(getattr(self, field_name), f"ResourcePressureProjection.{field_name}")
        ensure_score(self.resource_pressure_score, "ResourcePressureProjection.resource_pressure_score")
        ensure_bool(self.fatigue_reason, "ResourcePressureProjection.fatigue_reason")
        ensure_ref_text(self.real_resource_reason_ref, "ResourcePressureProjection.real_resource_reason_ref")
        ensure_bool(self.continue_with_low_energy_mode, "ResourcePressureProjection.continue_with_low_energy_mode")
        ensure_bool(self.resource_allocation_made, "ResourcePressureProjection.resource_allocation_made")
        if self.fatigue_reason or not self.continue_with_low_energy_mode or self.resource_allocation_made:
            raise ValueError("Resource pressure cannot masquerade as fatigue, force stop, or allocate resource")


@dataclass(frozen=True)
class CostEstimateHint(GovernanceArtifactBase):
    object_ref: str = "hint:l6_phase5_cost_estimate"
    estimate_summary_ref: str = "summary:l6_phase5_cost_estimate"
    reads_provider_prices: bool = False
    direct_budget_decision: bool = False
    run_budget_scope_ref: str = "run:l6_phase5_cost_scope"
    goal_budget_scope_ref: str = "goal:l6_phase5_cost_scope"
    actor_budget_scope_ref: str = "actor:l6_phase5_cost_scope"
    budget_owner_ref: str = "budget:l6_phase5_cost_owner"

    def __post_init__(self) -> None:
        super().__post_init__()
        for field_name in ("run_budget_scope_ref", "goal_budget_scope_ref", "actor_budget_scope_ref", "budget_owner_ref"):
            ensure_ref_text(getattr(self, field_name), f"CostEstimateHint.{field_name}")
        ensure_ref_text(self.estimate_summary_ref, "CostEstimateHint.estimate_summary_ref")
        ensure_bool(self.reads_provider_prices, "CostEstimateHint.reads_provider_prices")
        ensure_bool(self.direct_budget_decision, "CostEstimateHint.direct_budget_decision")
        if self.reads_provider_prices or self.direct_budget_decision:
            raise ValueError("Cost estimate hint is provider-neutral and non-decisional")


@dataclass(frozen=True)
class RateLimitRiskProjection(GovernanceArtifactBase):
    object_ref: str = "projection:l6_phase5_rate_limit_risk"
    rate_limit_risk_score: float = 0.4
    starts_rate_limiter: bool = False
    suggests_chunking: bool = True
    run_budget_scope_ref: str = "run:l6_phase5_rate_limit_scope"
    goal_budget_scope_ref: str = "goal:l6_phase5_rate_limit_scope"
    actor_budget_scope_ref: str = "actor:l6_phase5_rate_limit_scope"
    budget_owner_ref: str = "budget:l6_phase5_rate_limit_owner"
    live_limiter_started: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        for field_name in ("run_budget_scope_ref", "goal_budget_scope_ref", "actor_budget_scope_ref", "budget_owner_ref"):
            ensure_ref_text(getattr(self, field_name), f"RateLimitRiskProjection.{field_name}")
        ensure_score(self.rate_limit_risk_score, "RateLimitRiskProjection.rate_limit_risk_score")
        ensure_bool(self.starts_rate_limiter, "RateLimitRiskProjection.starts_rate_limiter")
        ensure_bool(self.suggests_chunking, "RateLimitRiskProjection.suggests_chunking")
        ensure_bool(self.live_limiter_started, "RateLimitRiskProjection.live_limiter_started")
        if self.starts_rate_limiter or self.live_limiter_started or not self.suggests_chunking:
            raise ValueError("RateLimitRiskProjection cannot start limiter")


@dataclass(frozen=True)
class ChunkingSuggestion(GovernanceArtifactBase):
    object_ref: str = "suggestion:l6_phase5_chunking"
    chunk_count_hint: int = 3
    suggestion_only: bool = True
    command_to_split: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        if not isinstance(self.chunk_count_hint, int) or self.chunk_count_hint < 1:
            raise ValueError("chunk_count_hint must be positive integer")
        ensure_bool(self.suggestion_only, "ChunkingSuggestion.suggestion_only")
        ensure_bool(self.command_to_split, "ChunkingSuggestion.command_to_split")
        if not self.suggestion_only or self.command_to_split:
            raise ValueError("ChunkingSuggestion is not a command")


@dataclass(frozen=True)
class HumanizedBudgetExhaustionStyleHint(GovernanceArtifactBase):
    object_ref: str = "hint:l6_phase5_humanized_budget_exhaustion_style"
    governance_reason_ref: str = "budget:l6_phase5_budget_exhausted"
    style_hint: str = "summary:humanized_budget_message_allowed_after_governance_reason"
    affective_reason_only: bool = False
    refusal_generated: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_text(self.governance_reason_ref, "HumanizedBudgetExhaustionStyleHint.governance_reason_ref")
        ensure_no_live_or_sensitive_text(self.style_hint, "HumanizedBudgetExhaustionStyleHint.style_hint")
        ensure_bool(self.affective_reason_only, "HumanizedBudgetExhaustionStyleHint.affective_reason_only")
        ensure_bool(self.refusal_generated, "HumanizedBudgetExhaustionStyleHint.refusal_generated")
        if self.affective_reason_only or self.refusal_generated:
            raise ValueError("Humanized budget message requires governance reason and remains a style hint")
