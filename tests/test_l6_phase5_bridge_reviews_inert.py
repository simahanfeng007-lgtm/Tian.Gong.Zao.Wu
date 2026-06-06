import pytest

from tiangong_kernel.l6_plugins.governance_control import *


def test_product_learning_healing_bridge_reviews_are_inert():
    assert ProductSpecSeedGovernanceReview().real_product_spec_generated is False
    assert ProductContextPrivacyCheck().writes_build_context is False
    assert ArtifactIntentRiskProjection().artifact_build_allowed is False
    assert BuildPlanRequirementHint().executes_build is False
    assert LearningNeedGovernanceReview().auto_learning_enabled is False
    assert RepairSuggestionRiskReview().auto_repair_enabled is False
    assert EvolutionCandidateSafetyReview().auto_evolution_enabled is False
    assert RollbackSuggestionGovernanceReview().auto_rollback_enabled is False
    assert MigrationSuggestionGovernanceReview().auto_migration_enabled is False
    assert HotSwitchReadinessGovernanceReview().performs_hot_switch is False
    with pytest.raises(ValueError):
        ProductSpecSeedGovernanceReview(real_product_spec_generated=True)
    with pytest.raises(ValueError):
        RepairSuggestionRiskReview(auto_repair_enabled=True)
