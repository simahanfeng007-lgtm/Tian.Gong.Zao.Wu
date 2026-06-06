from tiangong_kernel.l1_ports.model_provider_governance_ports import ModelCapabilityRequirement, ModelProviderRequirement


def test_l1_model_capability_requirement_serializable():
    req = ModelCapabilityRequirement(
        requirement_id="req:model:demo",
        provider_requirement=ModelProviderRequirement(allowed_provider_ids=("deepseek_v4", "gpt_5_5")),
    )
    data = req.to_dict()
    assert data["requirement_id"] == "req:model:demo"
    assert req.provider_requirement.provider_selection_is_policy_hint_only is True
