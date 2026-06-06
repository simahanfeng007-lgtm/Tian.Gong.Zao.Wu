from tiangong_kernel.l1_ports.model_provider_governance_ports import ModelProviderPort


def test_l1_model_provider_port_is_ref_only():
    port = ModelProviderPort(
        provider_id="mimo",
        provider_descriptor_ref="provider-descriptor-ref:mimo",
        capability_descriptor_ref="capability-descriptor-ref:mimo",
    )
    assert port.provider_id == "mimo"
    assert port.provider_neutral_only is True
    assert port.does_not_call_model is True
    assert port.does_not_decide_provider is True
