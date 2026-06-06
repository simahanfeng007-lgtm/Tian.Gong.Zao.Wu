from l3_phase7_builders import build_l3_phase7_objects
from tiangong_kernel.l3_orchestration import RecoveryEnvelopeStatus, RecoveryFlowKind


def test_recovery_request_and_flow_are_pure_advice():
    objects = build_l3_phase7_objects()
    request = objects["recovery_request"]
    envelope = objects["recovery_envelope"]
    flow = objects["recovery_flow"]
    assert request.request_only is True
    assert envelope.ref_only is True
    assert envelope.status is RecoveryEnvelopeStatus.READY_FOR_ADVICE
    assert flow.flow_kind is RecoveryFlowKind.REQUEST_RECOVERY_REVIEW
    assert flow.advisory_only is True
    assert not hasattr(request, "restore")
    assert not hasattr(flow, "engine")


def test_rollback_and_reversibility_are_suggestions_only():
    objects = build_l3_phase7_objects()
    rollback = objects["rollback_advice"]
    reversibility = objects["reversibility_review"]
    recovery_ranking = objects["recovery_ranking"]
    assert rollback.advisory_only is True
    assert rollback.rollback_need_score.advisory_only is True
    assert reversibility.advisory_only is True
    assert 0.0 <= reversibility.reversibility_score.value <= 1.0
    assert recovery_ranking.top_route_ref == recovery_ranking.candidates[0].route_ref
    assert not hasattr(rollback, "git")
    assert not hasattr(rollback, "apply_patch")
