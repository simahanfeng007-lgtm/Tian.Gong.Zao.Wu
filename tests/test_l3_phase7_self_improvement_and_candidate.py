from l3_phase7_builders import build_l3_phase7_objects
from tiangong_kernel.l3_orchestration import CandidateVerificationRouteKind, SelfImprovementFlowKind


def test_self_improvement_entries_do_not_auto_execute_or_escalate():
    objects = build_l3_phase7_objects()
    learning = objects["self_learning"]
    iteration = objects["self_iteration"]
    evolution = objects["self_evolution"]
    assert learning.flow_kind is SelfImprovementFlowKind.SELF_LEARNING
    assert iteration.flow_kind is SelfImprovementFlowKind.SELF_ITERATION
    assert evolution.flow_kind is SelfImprovementFlowKind.SELF_EVOLUTION
    assert learning.auto_execute is False
    assert iteration.auto_execute is False
    assert evolution.auto_execute is False
    assert learning.advisory_only is True
    assert not hasattr(evolution, "permission_grant")
    assert not hasattr(iteration, "hot_swap")


def test_candidate_change_and_patch_refs_are_ref_only():
    objects = build_l3_phase7_objects()
    change_ref = objects["change_ref"]
    patch_ref = objects["patch_ref"]
    evidence_chain = objects["evidence_chain"]
    ranking = objects["candidate_ranking"]
    assert change_ref.ref_only is True
    assert patch_ref.ref_only is True
    assert evidence_chain.ref_only is True
    assert ranking.candidates[0].route_kind is CandidateVerificationRouteKind.VALIDATE_FIRST
    assert objects["candidate_validation"].advisory_only is True
    assert objects["candidate_iteration"].advisory_only is True
    assert not hasattr(patch_ref, "patch_content")
    assert not hasattr(objects["candidate_evolution"], "merge")
