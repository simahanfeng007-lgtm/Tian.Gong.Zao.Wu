from l3_phase1_builders import typed
from l3_phase5_builders import build_l3_phase5_objects
from tiangong_kernel.l3_orchestration import (
    BoundaryExecutionRecommendation,
    RecommendationMode,
    ScoreDirection,
    build_boundary_clarification_need_score,
)


def test_boundary_execution_scores_are_explainable_and_advisory():
    objects = build_l3_phase5_objects()
    for key in (
        "boundary_completeness",
        "evidence_sufficiency",
        "clarification_need",
        "boundary_readiness",
        "precondition_score",
        "execution_readiness",
    ):
        score = objects[key]
        assert score.advisory_only is True, key
        assert 0.0 <= score.value <= 1.0, key
        assert score.reason_codes, key
    vector = objects["score_vector"]
    assert vector.score_entries
    assert any(entry[2] is ScoreDirection.COST for entry in vector.score_entries)


def test_boundary_execution_recommendation_is_not_l5_or_l4_result():
    objects = build_l3_phase5_objects()
    recommendation = objects["recommendation"]
    assert isinstance(recommendation, BoundaryExecutionRecommendation)
    assert recommendation.recommendation_mode is RecommendationMode.SUGGEST
    assert recommendation.advisory_only is True
    assert not hasattr(recommendation, "permission_grant")
    assert not hasattr(recommendation, "execution_result")
    assert not hasattr(recommendation, "confirmation_ticket")


def test_affective_and_dynamic_inputs_only_change_clarification_tendency():
    objects = build_l3_phase5_objects()
    base = build_boundary_clarification_need_score(
        typed(1702, "boundary_clarification_need_score"),
        objects["boundary_completeness"],
        objects["evidence_sufficiency"],
    )
    adjusted = build_boundary_clarification_need_score(
        typed(1703, "boundary_clarification_need_score"),
        objects["boundary_completeness"],
        objects["evidence_sufficiency"],
        affective_input=objects["phase3"]["math_input"].affective_input,
        dynamic_drive_input=objects["phase3"]["math_input"].dynamic_drive_input,
    )
    assert adjusted.value >= base.value
    assert adjusted.advisory_only is True
    assert not hasattr(adjusted, "risk_allow")
