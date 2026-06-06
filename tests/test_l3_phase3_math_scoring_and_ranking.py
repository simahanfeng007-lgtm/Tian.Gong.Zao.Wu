from dataclasses import replace

from l3_phase1_builders import typed
from l3_phase3_builders import build_l3_phase3_objects
from tiangong_kernel.l3_orchestration import (
    AffectiveWeightInput,
    DynamicDriveInput,
    RecommendationMode,
    ScoreDirection,
    ToolExposureCostScore,
    build_skill_tool_route_ranking,
    build_tool_exposure_cost_score,
)


def test_skill_tool_math_scores_are_advisory_and_explainable():
    objects = build_l3_phase3_objects()
    for key in ("skill_match", "skill_risk", "tool_minimality", "exposure_cost", "sufficiency", "reversibility", "stability"):
        score = objects[key]
        assert score.advisory_only is True, key
        assert 0.0 <= score.value <= 1.0, key
        assert score.reason_codes, key
    vector = objects["math_score_vector"]
    assert vector.score_entries
    assert any(entry[2] is ScoreDirection.COST for entry in vector.score_entries)


def test_skill_tool_recommendation_never_becomes_decision():
    objects = build_l3_phase3_objects()
    recommendation = objects["recommendation"]
    assert recommendation.recommendation_mode is RecommendationMode.SUGGEST
    assert recommendation.advisory_only is True
    assert not hasattr(recommendation, "decision")
    assert not hasattr(recommendation, "execution_token")


def test_affective_and_dynamic_inputs_only_change_exposure_tendency():
    objects = build_l3_phase3_objects()
    candidate = objects["tool_candidate_1"]
    base = build_tool_exposure_cost_score(candidate)
    affective_high_caution = AffectiveWeightInput(
        input_ref=typed(1100, "affective_weight_input"),
        caution_weight=1.0,
        confidence=0.8,
    )
    dynamic_high_risk = DynamicDriveInput(
        input_ref=typed(1101, "dynamic_drive_input"),
        risk_pressure_weight=1.0,
        confidence=0.8,
    )
    adjusted = build_tool_exposure_cost_score(candidate, affective_high_caution, dynamic_high_risk)
    assert isinstance(adjusted, ToolExposureCostScore)
    assert adjusted.value > base.value
    assert adjusted.advisory_only is True
    assert not hasattr(adjusted, "permission_grant")


def test_skill_tool_route_ranking_is_stable():
    objects = build_l3_phase3_objects()
    ranking = objects["route_ranking"]
    assert ranking.top_route_ref == objects["route_candidate_1"].route_ref
    changed = replace(objects["route_candidate_2"], skill_score=0.95, tool_group_score=0.95, exposure_cost=0.05)
    reranked = build_skill_tool_route_ranking(ranking.ranking_ref, (objects["route_candidate_1"], changed))
    assert reranked.target_scores[0][1] >= reranked.target_scores[1][1]
