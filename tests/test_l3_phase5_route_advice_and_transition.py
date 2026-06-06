from dataclasses import replace

from l3_phase1_builders import typed
from l3_phase5_builders import build_l3_phase5_objects
from tiangong_kernel.l3_orchestration import (
    BoundaryExecutionStateTransitionSuggestion,
    BoundaryRouteKind,
    ExecutionRouteKind,
    IntentToBoundaryAdvice,
    IntentToExecutionPreparationAdvice,
    build_boundary_route_ranking,
    build_execution_route_ranking,
)


def test_boundary_route_ranking_is_stable_and_advisory():
    objects = build_l3_phase5_objects()
    ranking = objects["boundary_ranking"]
    assert ranking.advisory_only is True
    assert ranking.top_route_ref == objects["boundary_candidate_1"].route_ref
    changed = replace(objects["boundary_candidate_2"], route_kind=BoundaryRouteKind.CONFIRMATION_PATH, readiness_score=0.99, evidence_score=0.99, clarification_need_score=0.0)
    reranked = build_boundary_route_ranking(typed(1700, "boundary_route_ranking"), (objects["boundary_candidate_1"], changed))
    assert reranked.target_scores[0][1] >= reranked.target_scores[1][1]
    assert not hasattr(ranking, "decision")


def test_execution_route_ranking_is_stable_and_not_dispatch_runtime():
    objects = build_l3_phase5_objects()
    ranking = objects["execution_ranking"]
    assert ranking.advisory_only is True
    assert ranking.top_route_ref == objects["execution_candidate_1"].route_ref
    changed = replace(objects["execution_candidate_2"], route_kind=ExecutionRouteKind.PREPARE_DISPATCH, readiness_score=0.99, precondition_score=0.99)
    reranked = build_execution_route_ranking(typed(1701, "execution_route_ranking"), (objects["execution_candidate_1"], changed))
    assert reranked.target_scores[0][1] >= reranked.target_scores[1][1]
    assert not hasattr(ranking, "dispatcher")


def test_intent_to_boundary_and_execution_links_are_references_only():
    objects = build_l3_phase5_objects()
    assert isinstance(objects["intent_to_boundary"], IntentToBoundaryAdvice)
    assert isinstance(objects["intent_to_execution"], IntentToExecutionPreparationAdvice)
    assert objects["intent_to_boundary"].advisory_only is True
    assert objects["intent_to_execution"].advisory_only is True
    assert isinstance(objects["state_transition"], BoundaryExecutionStateTransitionSuggestion)
    assert objects["state_transition"].advisory_only is True
