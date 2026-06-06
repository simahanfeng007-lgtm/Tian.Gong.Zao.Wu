from l4_phase3_builders import envelope
from tiangong_kernel.l4_action_grounding import AdapterMode, DryRunActionAdapter, FakeActionAdapter, InMemoryActionAdapter, NoOpActionAdapter


def payload(output):
    return dict(output.result_payload)


def test_l4_phase3_fake_adapter_is_test_only_and_no_real_action():
    adapter = FakeActionAdapter()
    output = adapter.invoke(envelope(mode=AdapterMode.FAKE))
    assert adapter.adapter_descriptor.test_only is True
    assert output.success is True
    assert payload(output)["adapter_result"] == "fake"
    assert output.real_action_performed is False


def test_l4_phase3_in_memory_adapter_uses_only_payload_memory():
    adapter = InMemoryActionAdapter(memory_items=(("memory_key", "memory_value"),))
    output = adapter.invoke(envelope(mode=AdapterMode.IN_MEMORY))
    assert payload(output)["memory_key"] == "memory_value"
    assert output.side_effect_summary == "in_memory_only"
    assert output.real_action_performed is False


def test_l4_phase3_dry_run_adapter_returns_preview_not_real_success():
    adapter = DryRunActionAdapter()
    output = adapter.invoke(envelope(mode=AdapterMode.DRY_RUN))
    values = payload(output)
    assert values["dry_run_only"] == "true"
    assert "preview" in values["side_effect_preview"]
    assert output.real_action_performed is False


def test_l4_phase3_no_op_adapter_always_no_ops():
    adapter = NoOpActionAdapter()
    output = adapter.invoke(envelope(mode=AdapterMode.NO_OP))
    assert payload(output)["adapter_result"] == "no_op"
    assert output.side_effect_summary == "none"
    assert output.real_action_performed is False
