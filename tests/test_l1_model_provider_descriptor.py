from tiangong_kernel.l1_ports.model_provider_governance_ports import (
    ModelProviderCapabilityDescriptor, ModelProviderRiskSurfaceDescriptor, ModelProviderDescriptor,
    ModelCredentialRequirementRef, ModelBudgetRequirementRef, ModelAuditRequirementRef, ModelPolicyRequirementRef,
    ModelProtocolFamily,
)


def test_l1_descriptor_can_express_provider():
    cap = ModelProviderCapabilityDescriptor(provider_id="glm_5_1", unknown_or_unverified_fields=("json_mode_supported",))
    risk = ModelProviderRiskSurfaceDescriptor(provider_id="glm_5_1")
    desc = ModelProviderDescriptor(
        provider_id="glm_5_1",
        provider_display_name="Z.AI GLM-5.1",
        protocol_families=(ModelProtocolFamily.OPENAI_CHAT_COMPLETIONS,),
        capability_descriptor=cap,
        risk_surface_descriptor=risk,
        credential_requirement_ref=ModelCredentialRequirementRef("cred-ref:glm"),
        budget_requirement_ref=ModelBudgetRequirementRef("budget-ref:glm"),
        audit_requirement_ref=ModelAuditRequirementRef("audit-ref:glm"),
        policy_requirement_ref=ModelPolicyRequirementRef("policy-ref:glm"),
    )
    assert desc.provider_id == "glm_5_1"
