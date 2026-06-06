from l4_phase4_builders import model_request, tool_request
from tiangong_kernel.l4_action_grounding import (
    DisabledRealModelToolAdapterStub,
    ModelActionFailureKind,
    NoLiveExecutionWithoutL5Invariant,
    ToolActionFailureKind,
)


def test_l4_phase4_no_live_model_action_without_l5_permit():
    request = model_request()
    assert request.permit_ref is None
    failure = DisabledRealModelToolAdapterStub().invoke_model_action(request)
    assert failure.failure_kind is ModelActionFailureKind.DISABLED_BY_DEFAULT
    assert failure.real_model_called is False


def test_l4_phase4_no_live_tool_action_without_l5_permit():
    request = tool_request()
    assert request.permit_ref is None
    failure = DisabledRealModelToolAdapterStub().disabled_tool_action(request)
    assert failure.failure_kind is ToolActionFailureKind.ADAPTER_DISABLED
    assert failure.real_tool_called is False


def test_l4_phase4_inherits_no_live_execution_without_l5_invariant():
    invariant = NoLiveExecutionWithoutL5Invariant(invariant_ref=tool_request().request_ref)
    assert invariant.invariant_name.startswith("NoLiveExecutionWithoutL5")
