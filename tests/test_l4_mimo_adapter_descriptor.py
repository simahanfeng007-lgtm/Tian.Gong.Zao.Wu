from tiangong_kernel.l4_action_grounding.model_provider_adapter import MiMoProviderDescriptor


def test_l4_provider_descriptor():
    desc = MiMoProviderDescriptor()
    assert desc.provider_id == "mimo"
    assert desc.disabled_by_default is True
    assert desc.requires_l5_permit is True
