from l3_phase1_builders import typed
from l3_phase6_builders import build_l3_phase6_objects
from tiangong_kernel.l3_orchestration import (
    RecommendationMode,
    SubsystemServiceRecommendation,
    build_candidate_priority_score,
)


def test_observation_context_service_scores_are_explainable_and_advisory():
    objects = build_l3_phase6_objects()
    score_keys = (
        "observation_credibility",
        "observation_relevance",
        "observation_completeness",
        "context_value",
        "context_continuity",
        "compression_score",
        "memory_need",
        "retrieval_need",
        "learning_signal_value",
        "learning_need",
        "affective_need",
        "candidate_priority",
        "candidate_learning_value",
        "subsystem_readiness",
    )
    for key in score_keys:
        score = objects[key]
        assert score.advisory_only is True, key
        assert 0.0 <= score.value <= 1.0, key
        assert score.reason_codes, key
    assert objects["score_vector"].score_entries


def test_affective_and_dynamic_inputs_only_change_candidate_priority_tendency():
    objects = build_l3_phase6_objects()
    base = build_candidate_priority_score(typed(1990, "candidate_priority_score"), objects["candidate_proposal"])
    adjusted = build_candidate_priority_score(
        typed(1991, "candidate_priority_score"),
        objects["candidate_proposal"],
        affective_input=objects["phase5"]["phase3"]["math_input"].affective_input,
        dynamic_drive_input=objects["phase5"]["phase3"]["math_input"].dynamic_drive_input,
    )
    assert adjusted.value >= base.value
    assert adjusted.advisory_only is True
    assert not hasattr(adjusted, "service_authorization")


def test_subsystem_route_recommendation_is_not_service_authorization():
    objects = build_l3_phase6_objects()
    recommendation = objects["recommendation"]
    assert isinstance(recommendation, SubsystemServiceRecommendation)
    assert recommendation.recommendation_mode is RecommendationMode.SUGGEST
    assert recommendation.advisory_only is True
    assert recommendation.recommended_service_request_ref is not None
    assert not hasattr(recommendation, "service_result")
    assert not hasattr(recommendation, "permission_grant")
