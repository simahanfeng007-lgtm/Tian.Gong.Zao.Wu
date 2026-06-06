from tiangong_kernel.l4_action_grounding.model_provider_adapter import MiniMaxM3ProviderDescriptor


def test_l4_provider_descriptor():
    desc = MiniMaxM3ProviderDescriptor()
    assert desc.provider_id == "minimax_m3"
    assert desc.disabled_by_default is True
    assert desc.requires_l5_permit is True
