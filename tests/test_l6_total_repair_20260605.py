import pytest

from tiangong_kernel.l6_plugins.common import (
    FailureReturnEnvelopeContract,
    L6ContractPatchQualityGateDecision,
    L6HotSwitchReadinessDeclaration,
    L6Phase2QualityGateDecision,
    ResultReturnEnvelopeContract,
    scan_l6_text,
)
from tiangong_kernel.l6_plugins.cognitive_continuity import (
    CandidateFactProposal,
    CanonicalMemoryField,
    CanonicalMemoryFieldSet,
    CognitiveOutputBase,
    ContextReentryEnvelope,
    ExplicitForgetRequestPriorityHint,
    FailureDiagnosisProjection,
    ForgettingReviewScore,
    GoalPriorityScore,
    L6Phase4CognitiveContinuityQualityGateDecision,
    MemoryEvidenceIndex,
    ProductBridgeReentryEnvelope,
    ProductContextSafetyProjection,
    ProductSpecSeedCandidate,
    RepairSuggestion,
    ScoreFormulaSpec,
    SelfHealingReentryEnvelope,
    SafeRepairSuggestion,
    scan_l6_phase4_text,
)
from tiangong_kernel.l6_plugins.governance_control import (
    BudgetPressureProjection,
    BudgetRequirement,
    EvidenceCompletenessScore,
    L6Phase5GovernanceQualityGateDecision,
    RateLimitRiskProjection,
    ResourcePressureProjection,
    scan_l6_phase5_text,
)
from tiangong_kernel.l6_plugins.mind import L6Phase3MindQualityGateDecision


def test_full_pytest_required_for_phase_entry_and_freeze_not_for_planning_continuation():
    assert L6Phase2QualityGateDecision().allow_enter_phase3 is False
    assert L6Phase2QualityGateDecision().allow_planning_continuation is True
    assert L6Phase2QualityGateDecision(full_pytest_passed_for_freeze=True).allow_enter_phase3 is True
    assert L6Phase3MindQualityGateDecision().allow_enter_phase4 is False
    assert L6Phase3MindQualityGateDecision(full_pytest_passed_for_freeze=True).allow_enter_phase4 is True
    assert L6Phase4CognitiveContinuityQualityGateDecision().allow_enter_phase5 is False
    assert L6Phase4CognitiveContinuityQualityGateDecision(full_pytest_passed_for_freeze=True).allow_enter_phase5 is True
    assert L6Phase5GovernanceQualityGateDecision().allow_enter_phase6 is False
    assert L6Phase5GovernanceQualityGateDecision(full_pytest_passed_for_freeze=True).allow_enter_phase6 is True
    assert L6ContractPatchQualityGateDecision().allow_freeze_contract_patch is False
    assert L6ContractPatchQualityGateDecision(full_pytest_passed_for_freeze=True).allow_freeze_contract_patch is True


def test_handoff_return_contracts_construct_and_remain_contract_only():
    assert ResultReturnEnvelopeContract().parent_handoff_required is True
    assert FailureReturnEnvelopeContract().failure_reason_required is True


def test_memory_package_keeps_six_fields_and_explicit_forget_review_only():
    fields = CanonicalMemoryFieldSet().field_names
    assert fields == tuple(CanonicalMemoryField)
    hint = ExplicitForgetRequestPriorityHint()
    assert hint.deletion_review_required is True
    assert hint.direct_delete_allowed is False
    score = ForgettingReviewScore(explicit_user_forget_request=1.0, protected_l5_rule_score=0.95)
    assert score.forced_forgetting_review_required is True
    assert score.l5_retention_conflict_review_required is True
    assert score.review_score == 1.0
    assert MemoryEvidenceIndex().full_memory_content_included is False


def test_math_score_spec_and_goal_priority_are_non_decisional():
    assert ScoreFormulaSpec().formula_is_decision is False
    assert 0 <= GoalPriorityScore().priority_score <= 1
    with pytest.raises(ValueError):
        ScoreFormulaSpec(formula_is_authorization=True)
    with pytest.raises(ValueError):
        GoalPriorityScore(becomes_execution_plan=True)


def test_learning_self_healing_and_product_candidates_are_review_only():
    assert FailureDiagnosisProjection().final_fault_assignment_allowed is False
    assert RepairSuggestion().executable_patch_included is False
    assert SafeRepairSuggestion().executable_patch_included is False
    assert SelfHealingReentryEnvelope().target_review_layer_ref == "review:l3_l5_self_healing_review"
    assert ProductSpecSeedCandidate().creates_product_spec is False
    assert ProductContextSafetyProjection().product_spec_context_created is False
    assert ProductBridgeReentryEnvelope().seed_refs == ("projection:l6_phase4_product_spec_seed_candidate",)
    with pytest.raises(ValueError):
        RepairSuggestion(executable_patch_included=True)


def test_budget_resource_and_audit_require_scope_refs_without_live_side_effects():
    assert BudgetRequirement().allocation_made is False
    assert BudgetPressureProjection().live_budget_decrement_made is False
    assert ResourcePressureProjection().resource_allocation_made is False
    assert RateLimitRiskProjection().live_limiter_started is False
    assert EvidenceCompletenessScore().score_is_permit is False
    with pytest.raises(ValueError):
        BudgetRequirement(high_permission_budget_bypass=True)
    with pytest.raises(ValueError):
        RateLimitRiskProjection(live_limiter_started=True)


def test_candidate_fact_context_and_tamper_refs_are_review_only():
    fact = CandidateFactProposal()
    assert fact.candidate_only is True
    assert fact.canonical_fact is False
    assert fact.l2_write_allowed is False
    assert ContextReentryEnvelope().direct_prompt_injection_allowed is False
    assert CognitiveOutputBase().tamper_evidence_ref.startswith("evidence:")


def test_forbidden_scan_rules_cover_new_hard_boundary_patterns():
    assert scan_l6_text("l6:dirty_budget", "decrement_budget reserve_quota DocxBuilder").passed is False
    assert scan_l6_phase4_text("l6:dirty_learning", "repair_applied auto_evolve ProductSpec(").passed is False
    assert scan_l6_phase5_text("l6:dirty_budget", "consume_budget start_limiter approve_execution").passed is False


def test_hot_switch_readiness_has_review_checkpoint_and_rollback_refs():
    readiness = L6HotSwitchReadinessDeclaration()
    assert readiness.checkpoint_ref.startswith("checkpoint:")
    assert readiness.rollback_route_ref.startswith("rollback:")
    assert readiness.performs_hot_switch is False
