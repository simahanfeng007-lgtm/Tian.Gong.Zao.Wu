from tiangong_kernel.l4_action_grounding.model_provider_adapter import GLM51ProviderDescriptor


def test_l4_provider_descriptor():
    desc = GLM51ProviderDescriptor()
    assert desc.provider_id == "glm_5_1"
    assert desc.disabled_by_default is True
    assert desc.requires_l5_permit is True
