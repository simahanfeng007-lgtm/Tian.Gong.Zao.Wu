from dataclasses import replace

from l3_phase1_builders import typed
from l3_phase4_builders import build_l3_phase4_objects
from tiangong_kernel.l3_orchestration import (
    IntentRecommendation,
    IntentRouteKind,
    RecommendationMode,
    ScoreDirection,
    build_intent_clarification_need_score,
    build_intent_route_ranking,
)


def test_intent_math_scores_are_explainable_and_advisory():
    objects = build_l3_phase4_objects()
    for key in ("generic_model_completeness", "ambiguity_score", "readiness_score", "degrade_score", "clarification_need"):
        score = objects[key]
        assert score.advisory_only is True, key
        assert 0.0 <= score.value <= 1.0, key
        assert score.reason_codes, key
    vector = objects["score_vector"]
    assert vector.score_entries
    assert any(entry[2] is ScoreDirection.COST for entry in vector.score_entries)


def test_intent_recommendation_never_becomes_decision_or_request():
    objects = build_l3_phase4_objects()
    recommendation = objects["recommendation"]
    assert isinstance(recommendation, IntentRecommendation)
    assert recommendation.recommendation_mode is RecommendationMode.SUGGEST
    assert recommendation.advisory_only is True
    assert not hasattr(recommendation, "decision")
    assert not hasattr(recommendation, "execution_request")
    assert not hasattr(recommendation, "boundary_check_request")


def test_affective_and_dynamic_inputs_only_change_clarification_tendency():
    objects = build_l3_phase4_objects()
    base = build_intent_clarification_need_score(
        typed(1300, "intent_clarification_need_score"),
        objects["ambiguity_score"],
        objects["generic_model_completeness"],
    )
    adjusted = build_intent_clarification_need_score(
        typed(1301, "intent_clarification_need_score"),
        objects["ambiguity_score"],
        objects["generic_model_completeness"],
        affective_input=objects["phase3"]["math_input"].affective_input,
        dynamic_drive_input=objects["phase3"]["math_input"].dynamic_drive_input,
    )
    assert adjusted.value >= base.value
    assert adjusted.advisory_only is True
    assert not hasattr(adjusted, "permission_grant")


def test_intent_route_ranking_is_stable():
    objects = build_l3_phase4_objects()
    ranking = objects["route_ranking"]
    assert ranking.top_route_ref == objects["route_candidate_1"].route_ref
    changed = replace(objects["route_candidate_2"], route_kind=IntentRouteKind.PREPARE_ACTION_REVIEW, readiness_score=0.99, completeness_score=0.99, ambiguity_score=0.0)
    reranked = build_intent_route_ranking(ranking.ranking_ref, (objects["route_candidate_1"], changed))
    assert reranked.target_scores[0][1] >= reranked.target_scores[1][1]
