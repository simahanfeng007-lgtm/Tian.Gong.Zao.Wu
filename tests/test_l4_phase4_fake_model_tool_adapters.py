from l4_phase4_builders import model_request, tool_request
from tiangong_kernel.l4_action_grounding import FakeModelAdapter, FakeToolAdapter


def test_l4_phase4_fake_model_adapter_returns_deterministic_result():
    adapter = FakeModelAdapter()
    output = adapter.invoke(model_request())
    assert adapter.adapter_descriptor.test_only is True
    assert output.fake_result is True
    assert output.real_model_called is False
    assert dict(output.payload_items)["model_result"] == "fake"


def test_l4_phase4_fake_tool_adapter_returns_deterministic_result():
    adapter = FakeToolAdapter()
    output = adapter.invoke(tool_request())
    assert adapter.adapter_descriptor.test_only is True
    assert output.fake_result is True
    assert output.real_tool_called is False
    assert dict(output.result_envelope.normalized_output)["tool_result"] == "fake"
