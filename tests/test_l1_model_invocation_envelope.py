from tiangong_kernel.l1_ports.model_provider_governance_ports import ModelCapabilityRequirement, ModelContextEnvelope, ModelInvocationEnvelope


def test_l1_invocation_envelope_is_provider_neutral():
    env = ModelInvocationEnvelope(
        invocation_id="invoke-ref:1",
        capability_requirement=ModelCapabilityRequirement(requirement_id="req-ref:1"),
        context_envelope=ModelContextEnvelope(context_ref="context-ref:1"),
    )
    assert env.provider_neutral_only is True
