import pytest

from tiangong_kernel.l6_plugins.cognitive_continuity import *


def test_learning_evolution_objects_do_not_auto_apply():
    assert LearningNeedProjection().starts_learning is False
    assert FailureDiagnosisProjection().assigns_fault_finally is False
    assert QualityGapReport().direct_fix_allowed is False
    assert RepairSuggestion().auto_repair_allowed is False
    assert EvolutionCandidate().applies_change is False
    assert IterationCandidate().applies_change is False
    assert RollbackSuggestion().auto_rollback_allowed is False
    assert MigrationSuggestion().auto_migration_allowed is False
    assert HotSwitchReadinessHint().is_permit is False
    assert LearningEvolutionReentryEnvelope().l3_l5_review_required is True
    with pytest.raises(ValueError):
        LearningNeedProjection(starts_learning=True)
    with pytest.raises(ValueError):
        RepairSuggestion(auto_repair_allowed=True)
    with pytest.raises(ValueError):
        EvolutionCandidate(applies_change=True)
    with pytest.raises(ValueError):
        RollbackSuggestion(auto_rollback_allowed=True)
    with pytest.raises(ValueError):
        HotSwitchReadinessHint(is_permit=True)


def test_self_healing_and_product_bridge_are_inert_future_bridges():
    assert HealingNeedProjection().starts_repair is False
    assert RecoveryCandidateProjection().auto_recover_allowed is False
    assert SafeRepairSuggestion().applies_patch is False
    assert SelfHealingReentryEnvelope().auto_heal_allowed is False
    assert ProductContextSafetyProjection().build_context_created is False
    assert ProductBridgeReentryEnvelope().build_action_allowed is False
    with pytest.raises(ValueError):
        HealingNeedProjection(starts_repair=True)
    with pytest.raises(ValueError):
        RecoveryCandidateProjection(auto_recover_allowed=True)
    with pytest.raises(ValueError):
        SafeRepairSuggestion(applies_patch=True)
    with pytest.raises(ValueError):
        ProductContextSafetyProjection(build_context_created=True)
    with pytest.raises(ValueError):
        ProductBridgeReentryEnvelope(build_action_allowed=True)


def test_l3_bridge_parser_and_conflict_set_do_not_dispatch_or_merge():
    assert L3CognitiveCandidateParser().requires_l5_reviewed_input is True
    assert L3CognitiveCandidateParser().emits_execution_plan is False
    assert CognitiveConflictSet().auto_merge_allowed is False
    assert CognitiveConflictSet().l3_l5_review_required is True
    assert L3CandidateDispatchHint().is_plan is False
    assert L3CandidateDispatchHint().is_permit is False
    with pytest.raises(ValueError):
        L3CognitiveCandidateParser(emits_execution_plan=True)
    with pytest.raises(ValueError):
        CognitiveConflictSet(auto_merge_allowed=True)
    with pytest.raises(ValueError):
        L3CandidateDispatchHint(is_plan=True)
