from tiangong_kernel.l4_action_grounding.model_provider_adapter import GPT55ProviderDescriptor


def test_l4_provider_descriptor():
    desc = GPT55ProviderDescriptor()
    assert desc.provider_id == "gpt_5_5"
    assert desc.disabled_by_default is True
    assert desc.requires_l5_permit is True
