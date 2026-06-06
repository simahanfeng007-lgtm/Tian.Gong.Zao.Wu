from dataclasses import replace

from l3_phase1_builders import typed
from l3_phase3_builders import build_l3_phase3_objects
from tiangong_kernel.l3_orchestration import (
    OrchestrationLifecycleKind,
    SkillDisplayCandidate,
    SkillVisibilityAdviceKind,
    build_skill_display_ranking,
)


def test_skill_display_selection_and_activation_are_advisory_only():
    objects = build_l3_phase3_objects()
    assert objects["display_advice"].advice_kind is SkillVisibilityAdviceKind.DISPLAY
    assert objects["display_advice"].advisory_only is True
    assert objects["selection_advice"].advisory_only is True
    assert objects["activation_advice"].advisory_only is True
    assert objects["activation_advice"].suggested_lifecycle is OrchestrationLifecycleKind.PREPARED
    assert not hasattr(objects["activation_advice"], "activation_token")
    assert not hasattr(objects["selection_advice"], "permission_grant")


def test_skill_display_ranking_is_stable_and_score_ordered():
    objects = build_l3_phase3_objects()
    ranking = objects["skill_ranking"]
    assert ranking.candidates[0].skill_ref == objects["skill_candidate_1"].skill_ref
    assert ranking.top_ranked_skill_ref == objects["skill_candidate_1"].skill_ref
    assert ranking.target_scores[0][1] >= ranking.target_scores[1][1]
    rebuilt = build_skill_display_ranking(ranking.ranking_ref, (objects["skill_candidate_2"], objects["skill_candidate_1"]))
    assert tuple(item.skill_ref for item in rebuilt.candidates) == tuple(item.skill_ref for item in ranking.candidates)


def test_skill_display_ranking_uses_stable_tie_breaker():
    c1 = SkillDisplayCandidate(
        candidate_ref=typed(1001, "skill_display_candidate"),
        skill_ref=typed(1002, "skill_ref"),
        match_score=0.5,
        readiness_score=0.5,
        continuity_score=0.5,
        risk_awareness_hint=0.5,
    )
    c2 = replace(c1, candidate_ref=typed(1003, "skill_display_candidate"), skill_ref=typed(1004, "skill_ref"))
    ranking = build_skill_display_ranking(typed(1005, "skill_display_ranking"), (c2, c1))
    assert ranking.candidates[0].skill_ref.ref_id.value < ranking.candidates[1].skill_ref.ref_id.value
