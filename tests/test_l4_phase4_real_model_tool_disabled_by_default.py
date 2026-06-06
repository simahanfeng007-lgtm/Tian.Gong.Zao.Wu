from l4_phase4_builders import model_request, tool_request
from tiangong_kernel.l4_action_grounding import DisabledRealModelToolAdapterStub, ModelActionFailureKind, ToolActionFailureKind


def test_l4_phase4_real_model_tool_stub_is_disabled_by_default():
    adapter = DisabledRealModelToolAdapterStub()
    descriptor = adapter.adapter_descriptor
    assert descriptor.enabled_by_default is False
    assert descriptor.production_enabled is False
    assert descriptor.requires_l5_permit is True


def test_l4_phase4_real_model_path_returns_disabled_failure():
    adapter = DisabledRealModelToolAdapterStub()
    failure = adapter.invoke_model_action(model_request())
    assert failure.failure_kind is ModelActionFailureKind.DISABLED_BY_DEFAULT
    assert failure.real_model_called is False


def test_l4_phase4_real_tool_path_returns_disabled_failure():
    adapter = DisabledRealModelToolAdapterStub()
    failure = adapter.disabled_tool_action(tool_request())
    assert failure.failure_kind is ToolActionFailureKind.ADAPTER_DISABLED
    assert failure.real_tool_called is False
    assert failure.failure_envelope.failure_code == "adapter_disabled"
