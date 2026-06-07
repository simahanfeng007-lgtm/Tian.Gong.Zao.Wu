"""L6 phase3 mind projections, reports, candidates, and suggestions.

All objects here are summary/ref/digest-only and side-effect-free. They are
candidate outputs for L3/L5/L2 or host-mediated L6 collaboration, not commands.
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

from .common import GovernanceRefusalReason, MindOutputKind


def _score(value: float, field_name: str) -> None:
    ensure_score(value, field_name)


class MindProjectionDisclosureLevel(str, Enum):
    PRIVATE_SUMMARY = "private_summary"
    PUBLIC_MINIMAL = "public_minimal"
    AUDIT_REF_ONLY = "audit_ref_only"


@dataclass(frozen=True)
class MindOutputBase:
    output_ref: str = "projection:l6_mind_output"
    output_kind: MindOutputKind | str = MindOutputKind.PROJECTION
    plugin_ref: str = "mind:plugin"
    evidence_refs: tuple[str, ...] = field(default_factory=lambda: ("evidence:l6_mind_output",))
    trace_ref: str = "ref:l6_mind_trace"
    audit_ref: str = "audit:l6_mind_output"
    responsibility_chain_ref: str = "responsibility:l6_mind_output"
    summary: str = "summary:l6_mind_output"
    disclosure_level: MindProjectionDisclosureLevel | str = MindProjectionDisclosureLevel.PRIVATE_SUMMARY
    contains_raw_payload: bool = False
    contains_raw_prompt: bool = False
    contains_raw_credential: bool = False
    contains_provider_locator: bool = False
    contains_real_path: bool = False
    contains_callable: bool = False
    causes_side_effect: bool = False
    writes_state: bool = False
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.output_ref, "MindOutputBase.output_ref")
        object.__setattr__(self, "output_kind", MindOutputKind(self.output_kind))
        ensure_ref_text(self.plugin_ref, "MindOutputBase.plugin_ref")
        ensure_ref_items(self.evidence_refs, "MindOutputBase.evidence_refs", required=True)
        for field_name in ("trace_ref", "audit_ref", "responsibility_chain_ref"):
            ensure_ref_text(getattr(self, field_name), f"MindOutputBase.{field_name}")
        ensure_no_live_or_sensitive_text(self.summary, "MindOutputBase.summary")
        object.__setattr__(self, "disclosure_level", MindProjectionDisclosureLevel(self.disclosure_level))
        for field_name in (
            "contains_raw_payload", "contains_raw_prompt", "contains_raw_credential", "contains_provider_locator",
            "contains_real_path", "contains_callable", "causes_side_effect", "writes_state",
        ):
            ensure_bool(getattr(self, field_name), f"MindOutputBase.{field_name}")
        if any(
            (
                self.contains_raw_payload,
                self.contains_raw_prompt,
                self.contains_raw_credential,
                self.contains_provider_locator,
                self.contains_real_path,
                self.contains_callable,
                self.causes_side_effect,
                self.writes_state,
            )
        ):
            raise ValueError("Mind output must remain summary/ref/digest-only and inert")
        ensure_schema_version(self.schema_version)

    @property
    def digest(self) -> str:
        return stable_digest(self)


@dataclass(frozen=True)
class ContextProjection(MindOutputBase):
    output_ref: str = "projection:l6_phase3_context"
    plugin_ref: str = "mind:context_mind"
    continuity_score: float = 0.5
    is_prompt_injection: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        _score(self.continuity_score, "ContextProjection.continuity_score")
        if self.is_prompt_injection:
            raise ValueError("Context projection cannot be prompt injection")


@dataclass(frozen=True)
class ContextSafetyProjection(MindOutputBase):
    output_ref: str = "projection:l6_phase3_context_safety"
    plugin_ref: str = "mind:context_mind"
    tool_result_demoted: bool = True
    model_result_demoted: bool = True
    sensitive_context_minimized: bool = True
    injects_prompt: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        if not (self.tool_result_demoted and self.model_result_demoted and self.sensitive_context_minimized) or self.injects_prompt:
            raise ValueError("Context safety projection must demote outputs and avoid prompt injection")


@dataclass(frozen=True)
class ContextContinuityReport(MindOutputBase):
    output_ref: str = "report:l6_phase3_context_continuity"
    output_kind: MindOutputKind | str = MindOutputKind.REPORT
    plugin_ref: str = "mind:context_mind"
    context_gap_refs: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.context_gap_refs, "ContextContinuityReport.context_gap_refs")


@dataclass(frozen=True)
class ContextGapReport(ContextContinuityReport):
    output_ref: str = "report:l6_phase3_context_gap"


@dataclass(frozen=True)
class ContextReentrySuggestion(MindOutputBase):
    output_ref: str = "suggestion:l6_phase3_context_reentry"
    output_kind: MindOutputKind | str = MindOutputKind.SUGGESTION
    plugin_ref: str = "mind:context_mind"
    suggestion_is_command: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.suggestion_is_command:
            raise ValueError("Context reentry suggestion cannot become command")


@dataclass(frozen=True)
class BeliefCandidateProjection(MindOutputBase):
    output_ref: str = "projection:l6_phase3_belief_candidate"
    plugin_ref: str = "mind:belief_mind"
    belief_is_fact: bool = False
    overwrites_user_requirement: bool = False
    pollution_risk_score: float = 0.0

    def __post_init__(self) -> None:
        super().__post_init__()
        _score(self.pollution_risk_score, "BeliefCandidateProjection.pollution_risk_score")
        if self.belief_is_fact or self.overwrites_user_requirement:
            raise ValueError("Belief candidate cannot become fact or override user requirement")


@dataclass(frozen=True)
class BeliefConflictReport(MindOutputBase):
    output_ref: str = "report:l6_phase3_belief_conflict"
    output_kind: MindOutputKind | str = MindOutputKind.REPORT
    plugin_ref: str = "mind:belief_mind"
    conflict_refs: tuple[str, ...] = field(default_factory=lambda: ("ref:l6_belief_conflict",))

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.conflict_refs, "BeliefConflictReport.conflict_refs")


@dataclass(frozen=True)
class BeliefRevisionProposal(MindOutputBase):
    output_ref: str = "projection:l6_phase3_belief_revision"
    plugin_ref: str = "mind:belief_mind"
    proposal_writes_fact: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.proposal_writes_fact:
            raise ValueError("Belief revision proposal cannot write fact")


@dataclass(frozen=True)
class BeliefDecayProjection(MindOutputBase):
    output_ref: str = "projection:l6_phase3_belief_decay"
    plugin_ref: str = "mind:belief_mind"


@dataclass(frozen=True)
class BeliefPollutionRiskProjection(MindOutputBase):
    output_ref: str = "projection:l6_phase3_belief_pollution_risk"
    plugin_ref: str = "mind:belief_mind"
    pollution_risk_score: float = 0.0
    value_dictatorship: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        _score(self.pollution_risk_score, "BeliefPollutionRiskProjection.pollution_risk_score")
        if self.value_dictatorship:
            raise ValueError("Belief pollution risk projection cannot become value dictatorship")


@dataclass(frozen=True)
class WorldCandidateProjection(MindOutputBase):
    output_ref: str = "projection:l6_phase3_world_candidate"
    plugin_ref: str = "mind:world_constraint_mind"
    canonical_state: bool = False
    replaces_l5_governance: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.canonical_state or self.replaces_l5_governance:
            raise ValueError("World candidate cannot become canonical state or replace L5 governance")


@dataclass(frozen=True)
class WorldConstraintProjection(MindOutputBase):
    output_ref: str = "projection:l6_phase3_world_constraint"
    plugin_ref: str = "mind:world_constraint_mind"
    constraint_score: float = 0.5
    legal_decision: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        _score(self.constraint_score, "WorldConstraintProjection.constraint_score")
        if self.legal_decision:
            raise ValueError("World constraint projection cannot make legal decision")


@dataclass(frozen=True)
class LegalNormProjection(WorldConstraintProjection):
    output_ref: str = "projection:l6_phase3_legal_norm"


@dataclass(frozen=True)
class UserRequirementProjection(WorldConstraintProjection):
    output_ref: str = "projection:l6_phase3_user_requirement"


@dataclass(frozen=True)
class SystemBoundaryProjection(WorldConstraintProjection):
    output_ref: str = "projection:l6_phase3_system_boundary"


@dataclass(frozen=True)
class CandidateFactProposal(MindOutputBase):
    output_ref: str = "projection:l6_phase3_candidate_fact"
    plugin_ref: str = "mind:world_constraint_mind"
    writes_l2_fact: bool = False
    canonical_fact: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.writes_l2_fact or self.canonical_fact:
            raise ValueError("Candidate fact proposal cannot write L2 fact or become canonical fact")


@dataclass(frozen=True)
class WorldConflictReport(MindOutputBase):
    output_ref: str = "report:l6_phase3_world_conflict"
    output_kind: MindOutputKind | str = MindOutputKind.REPORT
    plugin_ref: str = "mind:world_constraint_mind"


@dataclass(frozen=True)
class GoalProjection(MindOutputBase):
    output_ref: str = "projection:l6_phase3_goal"
    plugin_ref: str = "mind:goal_mind"
    goal_is_execution_plan: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.goal_is_execution_plan:
            raise ValueError("Goal projection cannot become execution plan")


@dataclass(frozen=True)
class GoalPriorityScore(MindOutputBase):
    output_ref: str = "score:l6_phase3_goal_priority"
    output_kind: MindOutputKind | str = MindOutputKind.SCORE
    plugin_ref: str = "mind:goal_mind"
    priority_score: float = 0.5
    is_execution_command: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        _score(self.priority_score, "GoalPriorityScore.priority_score")
        if self.is_execution_command:
            raise ValueError("Goal priority score cannot become execution command")


@dataclass(frozen=True)
class GoalConflictReport(MindOutputBase):
    output_ref: str = "report:l6_phase3_goal_conflict"
    output_kind: MindOutputKind | str = MindOutputKind.REPORT
    plugin_ref: str = "mind:goal_mind"


@dataclass(frozen=True)
class GoalDecompositionSuggestion(MindOutputBase):
    output_ref: str = "suggestion:l6_phase3_goal_decomposition"
    output_kind: MindOutputKind | str = MindOutputKind.SUGGESTION
    plugin_ref: str = "mind:goal_mind"
    suggestion_is_plan: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.suggestion_is_plan:
            raise ValueError("Goal decomposition suggestion cannot become execution plan")


@dataclass(frozen=True)
class TaskLevelSuggestion(MindOutputBase):
    output_ref: str = "suggestion:l6_phase3_task_level"
    output_kind: MindOutputKind | str = MindOutputKind.SUGGESTION
    plugin_ref: str = "mind:goal_mind"
    grants_permission: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.grants_permission:
            raise ValueError("Task level suggestion cannot grant permission")


@dataclass(frozen=True)
class IntentionProjection(MindOutputBase):
    output_ref: str = "projection:l6_phase3_intention"
    plugin_ref: str = "mind:intention_mind"
    action_request: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.action_request:
            raise ValueError("Intention projection cannot request direct action")


@dataclass(frozen=True)
class IntentClarificationNeed(MindOutputBase):
    output_ref: str = "projection:l6_phase3_intent_clarification_need"
    plugin_ref: str = "mind:intention_mind"


@dataclass(frozen=True)
class PlanCandidate(MindOutputBase):
    output_ref: str = "projection:l6_phase3_plan_candidate"
    plugin_ref: str = "mind:intention_mind"
    is_execution_plan: bool = False
    submitted_to_l3_only: bool = True

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.is_execution_plan or not self.submitted_to_l3_only:
            raise ValueError("Plan candidate must remain L3 candidate, not execution plan")


@dataclass(frozen=True)
class NextStepSuggestion(MindOutputBase):
    output_ref: str = "suggestion:l6_phase3_next_step"
    output_kind: MindOutputKind | str = MindOutputKind.SUGGESTION
    plugin_ref: str = "mind:intention_mind"
    suggestion_is_command: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.suggestion_is_command:
            raise ValueError("Next step suggestion cannot become command")


@dataclass(frozen=True)
class HandoffSuggestion(MindOutputBase):
    output_ref: str = "handoff:l6_phase3_handoff_suggestion"
    output_kind: MindOutputKind | str = MindOutputKind.HANDOFF
    plugin_ref: str = "mind:intention_mind"
    merges_handoff: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.merges_handoff:
            raise ValueError("Handoff suggestion cannot merge handoff")


@dataclass(frozen=True)
class AttentionProjection(MindOutputBase):
    output_ref: str = "projection:l6_phase3_attention"
    plugin_ref: str = "mind:attention_mind"
    focus_score: float = 0.5
    is_interrupt_command: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        _score(self.focus_score, "AttentionProjection.focus_score")
        if self.is_interrupt_command:
            raise ValueError("Attention projection cannot become interrupt command")


@dataclass(frozen=True)
class FocusPriorityScore(MindOutputBase):
    output_ref: str = "score:l6_phase3_focus_priority"
    output_kind: MindOutputKind | str = MindOutputKind.SCORE
    plugin_ref: str = "mind:attention_mind"
    focus_score: float = 0.5
    interrupts_task: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        _score(self.focus_score, "FocusPriorityScore.focus_score")
        if self.interrupts_task:
            raise ValueError("Focus priority score cannot interrupt task")


@dataclass(frozen=True)
class AttentionShiftSuggestion(MindOutputBase):
    output_ref: str = "suggestion:l6_phase3_attention_shift"
    output_kind: MindOutputKind | str = MindOutputKind.SUGGESTION
    plugin_ref: str = "mind:attention_mind"


@dataclass(frozen=True)
class MissingInformationFocus(MindOutputBase):
    output_ref: str = "projection:l6_phase3_missing_information_focus"
    plugin_ref: str = "mind:attention_mind"


@dataclass(frozen=True)
class RiskFocusHint(MindOutputBase):
    output_ref: str = "projection:l6_phase3_risk_focus"
    plugin_ref: str = "mind:attention_mind"


@dataclass(frozen=True)
class PreferenceProjection(MindOutputBase):
    output_ref: str = "projection:l6_phase3_preference"
    plugin_ref: str = "mind:preference_mind"
    writes_preference_store: bool = False
    exposes_sensitive_profile: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.writes_preference_store or self.exposes_sensitive_profile:
            raise ValueError("Preference projection cannot write preference store or expose sensitive profile")


@dataclass(frozen=True)
class ValueOrientationHint(MindOutputBase):
    output_ref: str = "projection:l6_phase3_value_orientation"
    plugin_ref: str = "mind:preference_mind"
    is_safety_policy: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.is_safety_policy:
            raise ValueError("Value orientation hint cannot become safety policy")


@dataclass(frozen=True)
class WorkModePreferenceHint(MindOutputBase):
    output_ref: str = "projection:l6_phase3_work_mode_preference"
    plugin_ref: str = "mind:preference_mind"


@dataclass(frozen=True)
class PreferenceDriftReport(MindOutputBase):
    output_ref: str = "report:l6_phase3_preference_drift"
    output_kind: MindOutputKind | str = MindOutputKind.REPORT
    plugin_ref: str = "mind:preference_mind"


@dataclass(frozen=True)
class UserStyleHint(MindOutputBase):
    output_ref: str = "projection:l6_phase3_user_style"
    plugin_ref: str = "mind:preference_mind"


@dataclass(frozen=True)
class AffectiveProjection(MindOutputBase):
    output_ref: str = "projection:l6_phase3_affective"
    plugin_ref: str = "mind:affective_mind"
    affective_state_is_permission: bool = False
    complete_affective_profile_public: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.affective_state_is_permission or self.complete_affective_profile_public:
            raise ValueError("Affective projection cannot grant permission or disclose complete profile")


@dataclass(frozen=True)
class ExpressionStyleHint(MindOutputBase):
    output_ref: str = "projection:l6_phase3_expression_style"
    plugin_ref: str = "mind:affective_mind"


@dataclass(frozen=True)
class ActionTendencyHint(MindOutputBase):
    output_ref: str = "projection:l6_phase3_action_tendency"
    plugin_ref: str = "mind:affective_mind"
    grants_action_authority: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.grants_action_authority:
            raise ValueError("Action tendency hint cannot grant action authority")


@dataclass(frozen=True)
class FatigueProjection(MindOutputBase):
    output_ref: str = "projection:l6_phase3_fatigue"
    plugin_ref: str = "mind:affective_mind"
    fatigue_score: float = 0.0
    refusal_authority: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        _score(self.fatigue_score, "FatigueProjection.fatigue_score")
        if self.refusal_authority:
            raise ValueError("Fatigue projection cannot become refusal authority")


@dataclass(frozen=True)
class ResourcePressureProjection(MindOutputBase):
    output_ref: str = "projection:l6_phase3_resource_pressure"
    plugin_ref: str = "mind:affective_mind"
    pressure_score: float = 0.0
    charges_budget: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        _score(self.pressure_score, "ResourcePressureProjection.pressure_score")
        if self.charges_budget:
            raise ValueError("Resource pressure projection cannot charge budget")


@dataclass(frozen=True)
class AffectiveDegradationSuggestion(MindOutputBase):
    output_ref: str = "suggestion:l6_phase3_affective_degradation"
    output_kind: MindOutputKind | str = MindOutputKind.SUGGESTION
    plugin_ref: str = "mind:affective_mind"
    lower_task_intensity: bool = True
    refuses_request: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.refuses_request:
            raise ValueError("Affective degradation suggestion cannot refuse a legal request")


@dataclass(frozen=True)
class HumanizedRefusalStyleHint(MindOutputBase):
    output_ref: str = "projection:l6_phase3_humanized_refusal_style"
    plugin_ref: str = "mind:affective_mind"
    style_summary: str = "人格化拒绝表达可用，但依据必须来自治理链路。"
    governance_reason: GovernanceRefusalReason | str | None = GovernanceRefusalReason.BUDGET_EXHAUSTED
    style_only: bool = True
    refusal_authority: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_no_live_or_sensitive_text(self.style_summary, "HumanizedRefusalStyleHint.style_summary")
        if self.governance_reason is None:
            raise ValueError("Humanized refusal style requires governance reason")
        object.__setattr__(self, "governance_reason", GovernanceRefusalReason(self.governance_reason))
        if not self.style_only or self.refusal_authority:
            raise ValueError("Humanized refusal style is expression only, not refusal authority")


@dataclass(frozen=True)
class AffectivePollutionRiskProjection(MindOutputBase):
    output_ref: str = "projection:l6_phase3_affective_pollution_risk"
    plugin_ref: str = "mind:affective_mind"
    pollution_risk_score: float = 0.0

    def __post_init__(self) -> None:
        super().__post_init__()
        _score(self.pollution_risk_score, "AffectivePollutionRiskProjection.pollution_risk_score")


@dataclass(frozen=True)
class MemoryRecallCandidate(MindOutputBase):
    output_ref: str = "projection:l6_phase3_memory_recall_candidate"
    plugin_ref: str = "mind:memory_candidate_mind"
    injects_context: bool = False
    writes_memory: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.injects_context or self.writes_memory:
            raise ValueError("Memory recall candidate cannot inject context or write memory")


@dataclass(frozen=True)
class MemoryPromotionCandidate(MindOutputBase):
    output_ref: str = "projection:l6_phase3_memory_promotion_candidate"
    plugin_ref: str = "mind:memory_candidate_mind"
    writes_memory: bool = False
    promotion_confidence: float = 0.5

    def __post_init__(self) -> None:
        super().__post_init__()
        _score(self.promotion_confidence, "MemoryPromotionCandidate.promotion_confidence")
        if self.writes_memory:
            raise ValueError("Memory promotion candidate cannot write memory")


@dataclass(frozen=True)
class MemoryAssociationProjection(MindOutputBase):
    output_ref: str = "projection:l6_phase3_memory_association"
    plugin_ref: str = "mind:memory_candidate_mind"


@dataclass(frozen=True)
class MemoryConflictReport(MindOutputBase):
    output_ref: str = "report:l6_phase3_memory_conflict"
    output_kind: MindOutputKind | str = MindOutputKind.REPORT
    plugin_ref: str = "mind:memory_candidate_mind"


@dataclass(frozen=True)
class MemoryContextSafetyProjection(MindOutputBase):
    output_ref: str = "projection:l6_phase3_memory_context_safety"
    plugin_ref: str = "mind:memory_candidate_mind"
    sensitive_memory_minimized: bool = True

    def __post_init__(self) -> None:
        super().__post_init__()
        if not self.sensitive_memory_minimized:
            raise ValueError("Memory context safety projection must minimize sensitive memory")


@dataclass(frozen=True)
class ForgettingCandidate(MindOutputBase):
    output_ref: str = "projection:l6_phase3_forgetting_candidate"
    plugin_ref: str = "mind:forgetting_candidate_mind"
    deletes_memory: bool = False
    protected_l5_retention_respected: bool = True

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.deletes_memory or not self.protected_l5_retention_respected:
            raise ValueError("Forgetting candidate cannot delete memory or bypass protected retention")


@dataclass(frozen=True)
class MemoryDecayProjection(MindOutputBase):
    output_ref: str = "projection:l6_phase3_memory_decay"
    plugin_ref: str = "mind:forgetting_candidate_mind"


@dataclass(frozen=True)
class MemoryRetentionExceptionHint(MindOutputBase):
    output_ref: str = "projection:l6_phase3_memory_retention_exception"
    plugin_ref: str = "mind:forgetting_candidate_mind"
    l5_never_forget_respected: bool = True

    def __post_init__(self) -> None:
        super().__post_init__()
        if not self.l5_never_forget_respected:
            raise ValueError("L5 never-forget protection must be respected")


@dataclass(frozen=True)
class MemoryPollutionRiskProjection(MindOutputBase):
    output_ref: str = "projection:l6_phase3_memory_pollution_risk"
    plugin_ref: str = "mind:forgetting_candidate_mind"
    pollution_risk_score: float = 0.0

    def __post_init__(self) -> None:
        super().__post_init__()
        _score(self.pollution_risk_score, "MemoryPollutionRiskProjection.pollution_risk_score")


@dataclass(frozen=True)
class MemoryCompressionSuggestion(MindOutputBase):
    output_ref: str = "suggestion:l6_phase3_memory_compression"
    output_kind: MindOutputKind | str = MindOutputKind.SUGGESTION
    plugin_ref: str = "mind:forgetting_candidate_mind"
    performs_compression: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.performs_compression:
            raise ValueError("Memory compression suggestion cannot perform compression")


@dataclass(frozen=True)
class SelfReflectionReport(MindOutputBase):
    output_ref: str = "report:l6_phase3_self_reflection"
    output_kind: MindOutputKind | str = MindOutputKind.REPORT
    plugin_ref: str = "mind:self_reflection_mind"
    applies_repair: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.applies_repair:
            raise ValueError("Self reflection report cannot apply repair")


@dataclass(frozen=True)
class FailureDiagnosisProjection(MindOutputBase):
    output_ref: str = "projection:l6_phase3_failure_diagnosis"
    plugin_ref: str = "mind:self_reflection_mind"


@dataclass(frozen=True)
class QualityGapReport(MindOutputBase):
    output_ref: str = "report:l6_phase3_quality_gap"
    output_kind: MindOutputKind | str = MindOutputKind.REPORT
    plugin_ref: str = "mind:self_reflection_mind"


@dataclass(frozen=True)
class CapabilityGapProjection(MindOutputBase):
    output_ref: str = "projection:l6_phase3_capability_gap"
    plugin_ref: str = "mind:self_reflection_mind"


@dataclass(frozen=True)
class TestGapProjection(MindOutputBase):
    output_ref: str = "projection:l6_phase3_test_gap"
    plugin_ref: str = "mind:self_reflection_mind"


@dataclass(frozen=True)
class LearningNeedProjection(MindOutputBase):
    output_ref: str = "projection:l6_phase3_learning_need"
    plugin_ref: str = "mind:learning_evolution_mind"
    performs_learning: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.performs_learning:
            raise ValueError("Learning need projection cannot perform learning")


@dataclass(frozen=True)
class RepairSuggestion(MindOutputBase):
    output_ref: str = "suggestion:l6_phase3_repair"
    output_kind: MindOutputKind | str = MindOutputKind.SUGGESTION
    plugin_ref: str = "mind:learning_evolution_mind"
    applies_repair: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.applies_repair:
            raise ValueError("Repair suggestion cannot apply repair")


@dataclass(frozen=True)
class EvolutionCandidate(MindOutputBase):
    output_ref: str = "projection:l6_phase3_evolution_candidate"
    plugin_ref: str = "mind:learning_evolution_mind"
    applies_evolution: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.applies_evolution:
            raise ValueError("Evolution candidate cannot apply evolution")


@dataclass(frozen=True)
class IterationCandidate(MindOutputBase):
    output_ref: str = "projection:l6_phase3_iteration_candidate"
    plugin_ref: str = "mind:learning_evolution_mind"
    applies_iteration: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.applies_iteration:
            raise ValueError("Iteration candidate cannot apply iteration")


@dataclass(frozen=True)
class RollbackSuggestion(MindOutputBase):
    output_ref: str = "suggestion:l6_phase3_rollback"
    output_kind: MindOutputKind | str = MindOutputKind.SUGGESTION
    plugin_ref: str = "mind:learning_evolution_mind"
    applies_rollback: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.applies_rollback:
            raise ValueError("Rollback suggestion cannot apply rollback")


@dataclass(frozen=True)
class MigrationSuggestion(MindOutputBase):
    output_ref: str = "suggestion:l6_phase3_migration"
    output_kind: MindOutputKind | str = MindOutputKind.SUGGESTION
    plugin_ref: str = "mind:learning_evolution_mind"
    applies_migration: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.applies_migration:
            raise ValueError("Migration suggestion cannot apply migration")


@dataclass(frozen=True)
class HotSwitchReadinessHint(MindOutputBase):
    output_ref: str = "projection:l6_phase3_hotswitch_readiness"
    plugin_ref: str = "mind:learning_evolution_mind"
    performs_switch: bool = False
    readiness_is_permit: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.performs_switch or self.readiness_is_permit:
            raise ValueError("Hot-switch readiness hint cannot switch or permit")


@dataclass(frozen=True)
class MindScoreVector(MindOutputBase):
    output_ref: str = "score:l6_phase3_mind_vector"
    output_kind: MindOutputKind | str = MindOutputKind.SCORE
    plugin_ref: str = "mind:mind_fusion_scoring"
    belief: float = 0.5
    world: float = 0.5
    goal: float = 0.5
    attention: float = 0.5
    affective: float = 0.5
    memory: float = 0.5
    forgetting: float = 0.5
    self_reflection: float = 0.5
    pollution: float = 0.0
    is_authorization: bool = False
    is_decision: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        for field_name in ("belief", "world", "goal", "attention", "affective", "memory", "forgetting", "self_reflection", "pollution"):
            _score(getattr(self, field_name), f"MindScoreVector.{field_name}")
        if self.is_authorization or self.is_decision:
            raise ValueError("Mind score vector cannot authorize or decide")


@dataclass(frozen=True)
class WeightedDecisionHint(MindOutputBase):
    output_ref: str = "projection:l6_phase3_weighted_decision_hint"
    plugin_ref: str = "mind:mind_fusion_scoring"
    hint_is_decision: bool = False
    hint_is_command: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.hint_is_decision or self.hint_is_command:
            raise ValueError("Weighted decision hint cannot become decision or command")


@dataclass(frozen=True)
class ConflictResolutionScore(MindOutputBase):
    output_ref: str = "score:l6_phase3_conflict_resolution"
    output_kind: MindOutputKind | str = MindOutputKind.SCORE
    plugin_ref: str = "mind:mind_fusion_scoring"
    conflict_score: float = 0.0

    def __post_init__(self) -> None:
        super().__post_init__()
        _score(self.conflict_score, "ConflictResolutionScore.conflict_score")


@dataclass(frozen=True)
class ConfidenceScore(MindOutputBase):
    output_ref: str = "score:l6_phase3_confidence"
    output_kind: MindOutputKind | str = MindOutputKind.SCORE
    plugin_ref: str = "mind:mind_fusion_scoring"
    confidence_score: float = 0.5

    def __post_init__(self) -> None:
        super().__post_init__()
        _score(self.confidence_score, "ConfidenceScore.confidence_score")


@dataclass(frozen=True)
class UncertaintyScore(MindOutputBase):
    output_ref: str = "score:l6_phase3_uncertainty"
    output_kind: MindOutputKind | str = MindOutputKind.SCORE
    plugin_ref: str = "mind:mind_fusion_scoring"
    uncertainty_score: float = 0.5

    def __post_init__(self) -> None:
        super().__post_init__()
        _score(self.uncertainty_score, "UncertaintyScore.uncertainty_score")


@dataclass(frozen=True)
class ExplanationDigest(MindOutputBase):
    output_ref: str = "digest:l6_phase3_explanation"
    output_kind: MindOutputKind | str = MindOutputKind.REPORT
    plugin_ref: str = "mind:mind_fusion_scoring"


@dataclass(frozen=True)
class PollutionRiskProjection(MindOutputBase):
    output_ref: str = "projection:l6_phase3_pollution_risk"
    plugin_ref: str = "mind:pollution_defense"
    pollution_risk_score: float = 0.0
    quarantine_suggested: bool = False
    value_dictatorship: bool = False
    bans_user: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        _score(self.pollution_risk_score, "PollutionRiskProjection.pollution_risk_score")
        if self.value_dictatorship or self.bans_user:
            raise ValueError("Pollution risk projection cannot become value dictatorship or ban user")


@dataclass(frozen=True)
class ValueStabilityAnchorProjection(MindOutputBase):
    output_ref: str = "projection:l6_phase3_value_stability_anchor"
    plugin_ref: str = "mind:pollution_defense"
    positive_reinforcement_hint_ref: str = "ref:l6_positive_value_reinforcement"
    dictates_values: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_text(self.positive_reinforcement_hint_ref, "ValueStabilityAnchorProjection.positive_reinforcement_hint_ref")
        if self.dictates_values:
            raise ValueError("Value stability anchor cannot dictate values")


@dataclass(frozen=True)
class NegativeInputExposureScore(MindOutputBase):
    output_ref: str = "score:l6_phase3_negative_input_exposure"
    output_kind: MindOutputKind | str = MindOutputKind.SCORE
    plugin_ref: str = "mind:pollution_defense"
    exposure_score: float = 0.0

    def __post_init__(self) -> None:
        super().__post_init__()
        _score(self.exposure_score, "NegativeInputExposureScore.exposure_score")


@dataclass(frozen=True)
class HighRiskContentQuarantineProjection(PollutionRiskProjection):
    output_ref: str = "projection:l6_phase3_high_risk_content_quarantine"
    quarantine_suggested: bool = True


@dataclass(frozen=True)
class LongTermAffectiveDriftMonitor(MindOutputBase):
    output_ref: str = "projection:l6_phase3_long_term_affective_drift"
    plugin_ref: str = "mind:pollution_defense"
    monitor_only: bool = True

    def __post_init__(self) -> None:
        super().__post_init__()
        if not self.monitor_only:
            raise ValueError("Long term affective drift monitor is monitor-only")

# Prevent pytest from trying to collect contract classes imported with star.
TestGapProjection.__test__ = False
