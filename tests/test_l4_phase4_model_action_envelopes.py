from l4_phase4_builders import model_request, phase4_ref
from tiangong_kernel.l4_action_grounding import (
    ModelActionFailure,
    ModelActionFailureKind,
    ModelActionRequest,
    ModelActionResult,
    action_grounding_stable_hash,
    action_grounding_to_primitive,
)


def test_l4_phase4_model_action_request_is_structural_and_serializable():
    request = model_request()
    assert isinstance(request, ModelActionRequest)
    assert request.request_only is True
    assert request.has_real_model_client is False
    primitive = action_grounding_to_primitive(request)
    assert primitive["dry_run"] is True
    assert action_grounding_stable_hash(request)


def test_l4_phase4_model_action_result_and_failure_are_standardized():
    request = model_request()
    result = ModelActionResult(
        result_ref=phase4_ref(30, "model_action_result"),
        request_ref=request.request_ref,
        output_ref=phase4_ref(31, "model_output"),
        usage_summary="preview",
    )
    failure = ModelActionFailure(
        failure_ref=phase4_ref(32, "model_action_failure"),
        request_ref=request.request_ref,
        failure_kind=ModelActionFailureKind.DRY_RUN_ONLY,
    )
    assert result.real_model_called is False
    assert failure.real_model_called is False
    assert failure.retry_allowed_hint is False
