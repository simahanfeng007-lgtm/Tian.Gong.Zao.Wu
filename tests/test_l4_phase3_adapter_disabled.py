from l4_phase3_builders import accepted_permit_and_gate, envelope
from tiangong_kernel.l4_action_grounding import AdapterMode, RealActionAdapterStub


def test_l4_phase3_real_adapter_stub_is_disabled_by_default():
    adapter = RealActionAdapterStub()
    descriptor = adapter.adapter_descriptor
    assert adapter.is_real_adapter is True
    assert descriptor.enabled_by_default is False
    assert descriptor.production_enabled is False
    assert descriptor.requires_l5_permit is True


def test_l4_phase3_real_adapter_stub_invoke_returns_disabled_failure_even_with_gate():
    permit, gate_result = accepted_permit_and_gate()
    adapter = RealActionAdapterStub()
    result = adapter.invoke(envelope(mode=AdapterMode.REAL_STUB, permit=permit, gate_result=gate_result))
    assert result.failure_code == "production_disabled"
    assert result.retry_allowed_hint is False
    assert result.real_action_performed is False
