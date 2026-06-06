from l3_phase7_builders import build_l3_phase7_objects
from tiangong_kernel.l3_orchestration import ValidationEnvelopeStatus, ValidationFlowKind


def test_validation_request_and_flow_are_request_and_advice_only():
    objects = build_l3_phase7_objects()
    request = objects["validation_request"]
    envelope = objects["validation_envelope"]
    flow = objects["validation_flow"]
    assert request.request_only is True
    assert envelope.ref_only is True
    assert envelope.status is ValidationEnvelopeStatus.READY_FOR_ADVICE
    assert flow.flow_kind is ValidationFlowKind.REQUEST_REVIEW
    assert flow.advisory_only is True
    assert not hasattr(request, "run_test")
    assert not hasattr(flow, "runner")


def test_validation_result_refs_and_retry_do_not_read_or_execute():
    objects = build_l3_phase7_objects()
    result = objects["validation_result"]
    retry = objects["validation_retry"]
    ranking = objects["validation_ranking"]
    assert result.ref_only is True
    assert retry.retry_only_as_advice is True
    assert ranking.top_route_ref == ranking.candidates[0].route_ref
    assert not hasattr(result, "read_report")
    assert not hasattr(retry, "execute_retry")
