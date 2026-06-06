from tiangong_kernel.l4_action_grounding.model_provider_adapter import ModelContextInputEnvelope, ModelProviderAdapterProtocol, DeepSeekV4DisabledStub


def test_l4_adapter_protocol_runtime_checkable():
    adapter = DeepSeekV4DisabledStub()
    assert isinstance(adapter, ModelProviderAdapterProtocol)
    result = adapter.invoke(ModelContextInputEnvelope(context_ref="context-ref:1"))
    assert result.failure_code == "l5_permit_required"
