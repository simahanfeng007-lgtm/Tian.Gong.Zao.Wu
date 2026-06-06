import pytest

from tiangong_kernel.l6_plugins.cognitive_continuity import *


def test_audit_chain_objects_have_refs_not_audit_writes():
    envelope = CognitiveAuditEnvelope()
    assert envelope.writes_audit_store is False
    assert envelope.grants_authorization is False
    assert envelope.evidence_refs
    assert envelope.redacted_evidence_refs
    assert len(envelope.digest) == 64
    assert MemoryCandidateEvidenceIndex().memory_candidate_refs
    assert CandidateFactAuditEnvelope().l2_write_allowed is False
    assert ReflectionLearningAuditRecord().auto_repair_allowed is False
    assert CognitiveReentryAuditEnvelope().l3_l5_review_required is True
    assert L6Phase4AuditPublicProjection().exposes_complete_evidence is False
    assert AuditCoverageReport().all_candidates_have_tamper_evidence is True
    with pytest.raises(ValueError):
        CognitiveAuditEnvelope(writes_audit_store=True)
    with pytest.raises(ValueError):
        CandidateFactAuditEnvelope(l2_write_allowed=True)
    with pytest.raises(ValueError):
        L6Phase4AuditPublicProjection(exposes_complete_evidence=True)
    with pytest.raises(ValueError):
        AuditCoverageReport(all_candidates_have_trace=False)


def test_budget_pressure_objects_are_not_budget_charges_or_limiters():
    assert ContextWindowPressureProjection().direct_truncation_allowed is False
    assert ToolLeasePressureProjection().direct_tool_stop_allowed is False
    assert MemoryCandidateBatchLimitHint().is_hard_limit is False
    assert BudgetAwareDegradationSuggestion().blocks_execution is False
    assert CandidateFactReviewBudgetHint().skip_fact_review_allowed is False
    assert WorldCandidateReviewPriorityHint().final_priority_decision is False
    assert SelfReflectionCostEstimate().auto_stop_allowed is False
    assert LearningNeedCostEstimate().auto_stop_allowed is False
    assert RepairSuggestionCostClass().auto_stop_allowed is False
    assert IterationCandidateBudgetPressureHint().auto_stop_allowed is False
    assert EvolutionCandidateCostRiskHint().auto_stop_allowed is False
    assert RefusalReasonIntegrityCheck().affective_reason_only is False
    assert ResourceBudgetReentryEnvelope().charges_budget is False
    with pytest.raises(ValueError):
        ContextWindowPressureProjection(direct_truncation_allowed=True)
    with pytest.raises(ValueError):
        MemoryCandidateBatchLimitHint(is_hard_limit=True)
    with pytest.raises(ValueError):
        BudgetAwareDegradationSuggestion(blocks_execution=True)
    with pytest.raises(ValueError):
        CandidateFactReviewBudgetHint(skip_fact_review_allowed=True)
    with pytest.raises(ValueError):
        ResourceBudgetReentryEnvelope(charges_budget=True)
