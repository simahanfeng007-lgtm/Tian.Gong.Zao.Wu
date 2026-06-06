from l4_phase4_builders import model_request, tool_request
from tiangong_kernel.l4_action_grounding import DryRunModelAdapter, DryRunToolAdapter


def test_l4_phase4_dry_run_model_adapter_returns_preview_only():
    adapter = DryRunModelAdapter()
    output = adapter.invoke(model_request())
    assert output.dry_run_only is True
    assert output.real_model_called is False
    assert dict(output.payload_items)["dry_run_only"] == "true"


def test_l4_phase4_dry_run_tool_adapter_returns_preview_only():
    adapter = DryRunToolAdapter()
    output = adapter.invoke(tool_request())
    assert output.dry_run_only is True
    assert output.real_tool_called is False
    assert dict(output.result_envelope.normalized_output)["dry_run_only"] == "true"
