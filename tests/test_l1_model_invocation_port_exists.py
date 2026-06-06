from tiangong_kernel.l1_ports.model_provider_governance_ports import ModelInvocationPort


def test_l1_model_invocation_port_preserves_l3_l5_l4_chain():
    port = ModelInvocationPort(
        invocation_port_id="invocation-port-ref:five-model",
        capability_requirement_ref="capability-requirement-ref:five-model",
        context_envelope_ref="context-envelope-ref:five-model",
        provider_requirement_ref="provider-requirement-ref:five-model",
    )
    assert port.dispatch_by_l3_required is True
    assert port.permit_by_l5_required is True
    assert port.adapter_by_l4_required is True
    assert port.provider_neutral_only is True
