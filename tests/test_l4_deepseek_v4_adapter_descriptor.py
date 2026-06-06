from tiangong_kernel.l4_action_grounding.model_provider_adapter import DeepSeekV4ProviderDescriptor


def test_l4_provider_descriptor():
    desc = DeepSeekV4ProviderDescriptor()
    assert desc.provider_id == "deepseek_v4"
    assert desc.disabled_by_default is True
    assert desc.requires_l5_permit is True
