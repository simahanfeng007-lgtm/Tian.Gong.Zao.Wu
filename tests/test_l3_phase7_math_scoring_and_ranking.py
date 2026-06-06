from l3_phase7_builders import build_l3_phase7_objects
from tiangong_kernel.l3_orchestration import (
    IterationEvolutionRecommendation,
    RecommendationMode,
    ScoreDirection,
    ValidationRecoveryRecommendation,
    build_evolution_pressure_score,
)
from l3_phase1_builders import typed


def test_validation_recovery_scores_and_recommendation_are_advisory():
    objects = build_l3_phase7_objects()
    for key in ("validation_value", "validation_readiness", "recovery_priority", "recovery_readiness", "rollback_need", "reversibility"):
        score = objects[key]
        assert 0.0 <= score.value <= 1.0, key
        assert score.advisory_only is True, key
    vector = objects["validation_recovery_vector"]
    assert any(entry[2] is ScoreDirection.COST for entry in vector.score_entries)
    recommendation = objects["validation_recovery_recommendation"]
    assert isinstance(recommendation, ValidationRecoveryRecommendation)
    assert recommendation.recommendation_mode is RecommendationMode.SUGGEST
    assert recommendation.advisory_only is True
    assert not hasattr(recommendation, "execute")
    assert not hasattr(recommendation, "rollback")


def test_iteration_evolution_scores_and_recommendation_are_advisory():
    objects = build_l3_phase7_objects()
    recommendation = objects["iteration_evolution_recommendation"]
    assert isinstance(recommendation, IterationEvolutionRecommendation)
    assert recommendation.recommendation_mode is RecommendationMode.SUGGEST
    assert recommendation.advisory_only is True
    assert objects["iteration_evolution_ranking"].top_route_ref == objects["iteration_ranking"].top_route_ref
    assert not hasattr(recommendation, "generate_patch")
    assert not hasattr(recommendation, "evolve")


def test_dynamic_hint_changes_evolution_pressure_only_as_score():
    objects = build_l3_phase7_objects()
    base = build_evolution_pressure_score(typed(2100, "evolution_pressure_score"), objects["iteration_need"], stability_pressure=0.1)
    adjusted = build_evolution_pressure_score(typed(2101, "evolution_pressure_score"), objects["iteration_need"], stability_pressure=0.6)
    assert adjusted.value >= base.value
    assert adjusted.advisory_only is True
    assert not hasattr(adjusted, "permission_grant")
