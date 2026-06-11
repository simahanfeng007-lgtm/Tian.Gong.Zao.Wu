"""Execution-first long-chain governance support declarations."""

from __future__ import annotations

from dataclasses import dataclass, field

from .common import GovernanceArtifactBase, ensure_bool, ensure_no_live_or_sensitive_text, ensure_ref_items, ensure_ref_text, ensure_score


@dataclass(frozen=True)
class LongChainGovernanceState(GovernanceArtifactBase):
    object_ref: str = "state:l6_phase5_long_chain_governance"
    phase_summary_ref: str = "summary:l6_phase5_long_chain_phase"
    checkpoint_hint_refs: tuple[str, ...] = field(default_factory=lambda: ("ref:l6_phase5_checkpoint_hint",))
    scheduler_state: bool = False
    self_schedules: bool = False
    execution_continuity_priority: bool = True

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_text(self.phase_summary_ref, "LongChainGovernanceState.phase_summary_ref")
        ensure_ref_items(self.checkpoint_hint_refs, "LongChainGovernanceState.checkpoint_hint_refs", required=True)
        for field_name in ("scheduler_state", "self_schedules", "execution_continuity_priority"):
            ensure_bool(getattr(self, field_name), f"LongChainGovernanceState.{field_name}")
        if self.scheduler_state or self.self_schedules or not self.execution_continuity_priority:
            raise ValueError("LongChainGovernanceState is not scheduler state and must preserve continuity")


@dataclass(frozen=True)
class LongChainRiskAccumulationProjection(GovernanceArtifactBase):
    object_ref: str = "projection:l6_phase5_long_chain_risk_accumulation"
    accumulated_risk_score: float = 0.45
    hard_boundary_triggered: bool = False
    ordinary_risk_blocks_task: bool = False
    risk_summary_refs: tuple[str, ...] = field(default_factory=lambda: ("summary:l6_phase5_risk_accumulation",))

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_score(self.accumulated_risk_score, "LongChainRiskAccumulationProjection.accumulated_risk_score")
        ensure_bool(self.hard_boundary_triggered, "LongChainRiskAccumulationProjection.hard_boundary_triggered")
        ensure_bool(self.ordinary_risk_blocks_task, "LongChainRiskAccumulationProjection.ordinary_risk_blocks_task")
        ensure_ref_items(self.risk_summary_refs, "LongChainRiskAccumulationProjection.risk_summary_refs", required=True)
        if self.ordinary_risk_blocks_task:
            raise ValueError("Ordinary risk must not block long-chain tasks by default")


@dataclass(frozen=True)
class LongChainBudgetPressureProjection(GovernanceArtifactBase):
    object_ref: str = "projection:l6_phase5_long_chain_budget_pressure"
    pressure_score: float = 0.5
    degrade_before_abort: bool = True
    aborts_on_pressure: bool = False
    budget_summary_refs: tuple[str, ...] = field(default_factory=lambda: ("summary:l6_phase5_budget_pressure",))

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_score(self.pressure_score, "LongChainBudgetPressureProjection.pressure_score")
        ensure_bool(self.degrade_before_abort, "LongChainBudgetPressureProjection.degrade_before_abort")
        ensure_bool(self.aborts_on_pressure, "LongChainBudgetPressureProjection.aborts_on_pressure")
        ensure_ref_items(self.budget_summary_refs, "LongChainBudgetPressureProjection.budget_summary_refs", required=True)
        if not self.degrade_before_abort or self.aborts_on_pressure:
            raise ValueError("Long-chain budget pressure should degrade, not abort")


@dataclass(frozen=True)
class LongChainAuditContinuityProjection(GovernanceArtifactBase):
    object_ref: str = "projection:l6_phase5_long_chain_audit_continuity"
    audit_segment_refs: tuple[str, ...] = field(default_factory=lambda: ("audit:l6_phase5_segment",))
    continuity_score: float = 0.9
    writes_audit_store: bool = False
    complete_chain_public: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.audit_segment_refs, "LongChainAuditContinuityProjection.audit_segment_refs", required=True)
        ensure_score(self.continuity_score, "LongChainAuditContinuityProjection.continuity_score")
        ensure_bool(self.writes_audit_store, "LongChainAuditContinuityProjection.writes_audit_store")
        ensure_bool(self.complete_chain_public, "LongChainAuditContinuityProjection.complete_chain_public")
        if self.writes_audit_store or self.complete_chain_public:
            raise ValueError("Audit continuity projection is ref-only")


@dataclass(frozen=True)
class LongChainCheckpointHint(GovernanceArtifactBase):
    object_ref: str = "ref:l6_phase5_checkpoint_hint"
    current_stage_ref: str = "summary:l6_phase5_current_stage"
    completed_summary_ref: str = "summary:l6_phase5_completed"
    pending_summary_ref: str = "summary:l6_phase5_pending"
    next_action_hint_ref: str = "hint:l6_phase5_next_action"
    stored_as_file: bool = False
    scheduler_state: bool = False
    direct_resume_action: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        for field_name in ("current_stage_ref", "completed_summary_ref", "pending_summary_ref", "next_action_hint_ref"):
            ensure_ref_text(getattr(self, field_name), f"LongChainCheckpointHint.{field_name}")
        for field_name in ("stored_as_file", "scheduler_state", "direct_resume_action"):
            ensure_bool(getattr(self, field_name), f"LongChainCheckpointHint.{field_name}")
        if self.stored_as_file or self.scheduler_state or self.direct_resume_action:
            raise ValueError("LongChainCheckpointHint cannot be file write, scheduler state, or direct action")


@dataclass(frozen=True)
class LongChainMinimalConfirmationPolicy(GovernanceArtifactBase):
    object_ref: str = "policy:l6_phase5_long_chain_minimal_confirmation"
    batch_safe_confirmations: bool = True
    defer_low_risk_confirmations: bool = True
    ask_every_step: bool = False
    hard_boundary_review_refs: tuple[str, ...] = field(default_factory=lambda: ("policy:a5", "policy:credential", "policy:irreversible"))

    def __post_init__(self) -> None:
        super().__post_init__()
        for field_name in ("batch_safe_confirmations", "defer_low_risk_confirmations", "ask_every_step"):
            ensure_bool(getattr(self, field_name), f"LongChainMinimalConfirmationPolicy.{field_name}")
        ensure_ref_items(self.hard_boundary_review_refs, "LongChainMinimalConfirmationPolicy.hard_boundary_review_refs", required=True)
        if not self.batch_safe_confirmations or not self.defer_low_risk_confirmations or self.ask_every_step:
            raise ValueError("Long-chain minimal confirmation must avoid safe over-confirmation")


@dataclass(frozen=True)
class LongChainContinuationHint(GovernanceArtifactBase):
    object_ref: str = "hint:l6_phase5_long_chain_continuation"
    should_continue_when_safe: bool = True
    bypasses_hard_boundaries: bool = False
    low_risk_should_continue: bool = True
    reversible_candidate_should_continue: bool = True
    continuation_summary: str = "summary:continue_with_reviewed_boundaries"

    def __post_init__(self) -> None:
        super().__post_init__()
        for field_name in ("should_continue_when_safe", "bypasses_hard_boundaries", "low_risk_should_continue", "reversible_candidate_should_continue"):
            ensure_bool(getattr(self, field_name), f"LongChainContinuationHint.{field_name}")
        ensure_no_live_or_sensitive_text(self.continuation_summary, "LongChainContinuationHint.continuation_summary")
        if not self.should_continue_when_safe or self.bypasses_hard_boundaries or not self.low_risk_should_continue or not self.reversible_candidate_should_continue:
            raise ValueError("LongChainContinuationHint must continue safe work without bypassing hard boundaries")


@dataclass(frozen=True)
class LongChainDegradedContinuationSuggestion(GovernanceArtifactBase):
    object_ref: str = "suggestion:l6_phase5_long_chain_degraded_continuation"
    degrade_not_abort: bool = True
    continue_readonly: bool = True
    pause_high_cost_branch: bool = True
    aborts_task: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        for field_name in ("degrade_not_abort", "continue_readonly", "pause_high_cost_branch", "aborts_task"):
            ensure_bool(getattr(self, field_name), f"LongChainDegradedContinuationSuggestion.{field_name}")
        if not self.degrade_not_abort or not self.continue_readonly or not self.pause_high_cost_branch or self.aborts_task:
            raise ValueError("Long-chain degradation should continue, not abort")


@dataclass(frozen=True)
class LongChainRecoverySuggestion(GovernanceArtifactBase):
    object_ref: str = "suggestion:l6_phase5_long_chain_recovery"
    recovery_summary_ref: str = "summary:l6_phase5_recovery"
    checkpoint_hint_ref: str = "ref:l6_phase5_checkpoint_hint"
    direct_replay: bool = False
    self_migrates: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_text(self.recovery_summary_ref, "LongChainRecoverySuggestion.recovery_summary_ref")
        ensure_ref_text(self.checkpoint_hint_ref, "LongChainRecoverySuggestion.checkpoint_hint_ref")
        ensure_bool(self.direct_replay, "LongChainRecoverySuggestion.direct_replay")
        ensure_bool(self.self_migrates, "LongChainRecoverySuggestion.self_migrates")
        if self.direct_replay or self.self_migrates:
            raise ValueError("LongChainRecoverySuggestion cannot replay or migrate")


@dataclass(frozen=True)
class ExecutionContinuityPriorityHint(GovernanceArtifactBase):
    object_ref: str = "hint:l6_phase5_execution_continuity_priority"
    policy_ref: str = "policy:execution_first_within_hard_boundaries"
    execution_first: bool = True
    bypass_hard_boundaries: bool = False
    summarizes_not_interrupts: bool = True

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_text(self.policy_ref, "ExecutionContinuityPriorityHint.policy_ref")
        for field_name in ("execution_first", "bypass_hard_boundaries", "summarizes_not_interrupts"):
            ensure_bool(getattr(self, field_name), f"ExecutionContinuityPriorityHint.{field_name}")
        if not self.execution_first or self.bypass_hard_boundaries or not self.summarizes_not_interrupts:
            raise ValueError("Execution continuity priority must preserve hard boundaries")


@dataclass(frozen=True)
class LongChainGovernanceSummary(GovernanceArtifactBase):
    object_ref: str = "summary:l6_phase5_long_chain_governance"
    checkpoint_hint_refs: tuple[str, ...] = field(default_factory=lambda: ("ref:l6_phase5_checkpoint_hint",))
    recovery_hint_refs: tuple[str, ...] = field(default_factory=lambda: ("suggestion:l6_phase5_long_chain_recovery",))
    minimal_confirmation_ref: str = "policy:l6_phase5_long_chain_minimal_confirmation"
    continues_low_risk: bool = True
    interrupts_by_default: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.checkpoint_hint_refs, "LongChainGovernanceSummary.checkpoint_hint_refs", required=True)
        ensure_ref_items(self.recovery_hint_refs, "LongChainGovernanceSummary.recovery_hint_refs", required=True)
        ensure_ref_text(self.minimal_confirmation_ref, "LongChainGovernanceSummary.minimal_confirmation_ref")
        ensure_bool(self.continues_low_risk, "LongChainGovernanceSummary.continues_low_risk")
        ensure_bool(self.interrupts_by_default, "LongChainGovernanceSummary.interrupts_by_default")
        if not self.continues_low_risk or self.interrupts_by_default:
            raise ValueError("LongChainGovernanceSummary must support execution continuity")
