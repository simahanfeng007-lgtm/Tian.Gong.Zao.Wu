import pytest

from l4_phase4_builders import phase4_ref, tool_arguments, tool_call, tool_request
from tiangong_kernel.l4_action_grounding import (
    ToolActionFailure,
    ToolActionFailureKind,
    ToolActionRequest,
    ToolArgumentEnvelope,
    ToolFailureEnvelope,
    ToolResultEnvelope,
    action_grounding_stable_hash,
    action_grounding_to_primitive,
)


def test_l4_phase4_tool_action_request_and_call_envelopes_are_structural():
    request = tool_request()
    assert isinstance(request, ToolActionRequest)
    assert request.resolves_tool_registry is False
    assert request.exposes_tool_to_model is False
    assert request.real_tool_called is False
    primitive = action_grounding_to_primitive(request)
    assert primitive["dry_run"] is True
    assert action_grounding_stable_hash(tool_call())


def test_l4_phase4_tool_argument_envelope_rejects_plain_credential_flag():
    args = tool_arguments()
    assert dict(args.argument_items)["query"] == "hello"
    with pytest.raises(ValueError):
        ToolArgumentEnvelope(argument_ref=phase4_ref(40, "tool_argument"), contains_plain_credential=True)


def test_l4_phase4_tool_result_and_failure_envelopes_are_standardized():
    result = ToolResultEnvelope(
        result_ref=phase4_ref(41, "tool_result"),
        normalized_output=(("status", "dry_run"),),
        resource_usage_summary="preview",
    )
    failure_envelope = ToolFailureEnvelope(
        failure_ref=phase4_ref(42, "tool_failure_envelope"),
        failure_code="argument_invalid",
        message="argument invalid",
    )
    failure = ToolActionFailure(
        failure_ref=phase4_ref(43, "tool_action_failure"),
        failure_kind=ToolActionFailureKind.ARGUMENT_INVALID,
        failure_envelope=failure_envelope,
    )
    assert result.real_tool_called is False
    assert failure.real_tool_called is False
    assert failure.failure_envelope.failure_code == "argument_invalid"
