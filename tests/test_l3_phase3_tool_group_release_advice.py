from l3_phase3_builders import build_l3_phase3_objects
from tiangong_kernel.l3_orchestration import ToolGroupAdviceKind, build_tool_group_release_ranking


def test_tool_group_release_advice_is_not_real_release():
    objects = build_l3_phase3_objects()
    release_advice = objects["release_advice"]
    lease_advice = objects["lease_advice"]
    assert release_advice.advice_kind is ToolGroupAdviceKind.RELEASE
    assert release_advice.advisory_only is True
    assert lease_advice.advisory_only is True
    assert not hasattr(release_advice, "released_tools")
    assert not hasattr(lease_advice, "lease_token")
    assert not hasattr(lease_advice, "permission_grant")


def test_tool_group_ranking_prefers_minimal_sufficient_candidate():
    objects = build_l3_phase3_objects()
    ranking = objects["tool_ranking"]
    assert ranking.top_tool_group_ref == objects["tool_candidate_1"].tool_group_ref
    assert ranking.target_scores[0][1] >= ranking.target_scores[1][1]
    rebuilt = build_tool_group_release_ranking(
        ranking.ranking_ref,
        (objects["tool_candidate_2"], objects["tool_candidate_1"]),
    )
    assert tuple(item.tool_group_ref for item in rebuilt.candidates) == tuple(item.tool_group_ref for item in ranking.candidates)


def test_tool_group_minimal_release_advice_has_explanation():
    objects = build_l3_phase3_objects()
    advice = objects["minimal_release_advice"]
    assert advice.kept_tool_refs
    assert advice.omitted_tool_refs
    assert advice.minimality_score > 0.0
    assert advice.reason_codes
