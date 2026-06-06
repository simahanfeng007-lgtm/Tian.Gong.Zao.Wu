from l3_phase6_builders import build_l3_phase6_objects
from tiangong_kernel.l3_orchestration import (
    CandidateProposalKind,
    ObservationContextTransitionKind,
)


def test_candidate_proposal_flow_is_advice_only():
    objects = build_l3_phase6_objects()
    proposal = objects["candidate_proposal"]
    promotion = objects["candidate_promotion"]
    reject = objects["candidate_reject"]
    candidate_ranking = objects["candidate_ranking"]
    assert proposal.proposal_kind is CandidateProposalKind.LEARNING
    assert proposal.advisory_only is True
    assert promotion.advisory_only is True
    assert reject.advisory_only is True
    assert candidate_ranking.top_candidate_ref == proposal.candidate_ref
    assert not hasattr(proposal, "apply_patch")
    assert not hasattr(proposal, "auto_merge")


def test_front_five_stage_connection_advices_are_refs_only():
    objects = build_l3_phase6_objects()
    assert objects["execution_to_observation"].transition_kind is ObservationContextTransitionKind.EXECUTION_TO_OBSERVATION
    assert objects["execution_result_context"].transition_kind is ObservationContextTransitionKind.RESULT_TO_CONTEXT
    assert objects["intent_observation_feedback"].transition_kind is ObservationContextTransitionKind.INTENT_TO_OBSERVATION_FEEDBACK
    assert objects["skill_tool_context"].transition_kind is ObservationContextTransitionKind.SKILL_TOOL_TO_CONTEXT
    for key in (
        "run_observation",
        "task_observation",
        "turn_observation",
        "step_observation",
        "run_service",
        "task_service",
        "turn_service",
        "step_service",
    ):
        assert objects[key].advisory_only is True, key
