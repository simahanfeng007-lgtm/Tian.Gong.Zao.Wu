from tiangong_kernel.l5_plugin_host.model_capability_invariants import ModelInvocationPermit, ModelProviderPermitScope, ModelInvocationBudgetPermitRef, ModelInvocationAuditRequirementRef, ModelInvocationCredentialHandleRef


def test_l5_model_invocation_permit_is_not_client():
    permit = ModelInvocationPermit(
        permit_ref="permit-ref:1",
        provider_scope=ModelProviderPermitScope(allowed_provider_ids=("gpt_5_5",)),
        budget_permit_ref=ModelInvocationBudgetPermitRef("budget-ref:1"),
        audit_requirement_ref=ModelInvocationAuditRequirementRef("audit-ref:1"),
        credential_handle_ref=ModelInvocationCredentialHandleRef("cred-ref:1"),
        policy_permit_ref="policy-ref:1",
        context_policy_ref="context-policy-ref:1",
    )
    assert permit.permit_only is True
    assert permit.not_a_model_client is True
