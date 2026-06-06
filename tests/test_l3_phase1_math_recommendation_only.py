from dataclasses import fields

from l3_phase1_builders import build_l3_objects
from tiangong_kernel.l3_orchestration import MathRecommendation, RouteRanking, StateTransitionAdvice


FORBIDDEN_FIELD_FRAGMENTS = (
    "permit",
    "permission",
    "authorize",
    "approval",
    "grant",
    "lease",
    "final_execute",
    "execute_allowed",
    "tool_release",
    "skill_select",
)


def test_l3_phase1_math_recommendation_route_and_transition_are_advisory_only():
    objects = build_l3_objects()
    recommendation = objects["recommendation"]
    ranking = objects["ranking"]
    advice = objects["transition_advice"]
    assert isinstance(recommendation, MathRecommendation)
    assert isinstance(ranking, RouteRanking)
    assert isinstance(advice, StateTransitionAdvice)
    assert recommendation.advisory_only is True
    assert ranking.advisory_only is True
    assert advice.advisory_only is True
    assert recommendation.boundary_review_refs
    assert advice.boundary_review_refs


def test_l3_phase1_recommendation_objects_do_not_define_permission_or_tool_release_fields():
    for cls in (MathRecommendation, RouteRanking, StateTransitionAdvice):
        names = {field.name for field in fields(cls)}
        for name in names:
            assert not any(fragment in name for fragment in FORBIDDEN_FIELD_FRAGMENTS), (cls.__name__, name)
