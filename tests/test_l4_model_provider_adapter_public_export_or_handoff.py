import tiangong_kernel.l4_action_grounding as l4


def test_l4_model_provider_adapter_public_exports():
    assert hasattr(l4, "ModelProviderAdapterProtocol")
    assert hasattr(l4, "MiMoTokenPlanRequestMapper")
    assert hasattr(l4, "MiMoOrdinaryApiRequestMapper")
    assert hasattr(l4, "mimo_api_surface_descriptors")
    assert "MiMoTokenPlanRequestMapper" in l4.__all__
