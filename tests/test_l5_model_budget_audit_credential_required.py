from tiangong_kernel.l5_plugin_host.model_capability_invariants import ModelCredentialHandleOnlyPolicy, ModelBudgetRequiredPolicy, ModelAuditRequiredPolicy, ModelContextPolicyRequired


def test_l5_model_access_requires_budget_audit_credential_context_policy():
    assert ModelCredentialHandleOnlyPolicy().credential_handle_required is True
    assert ModelBudgetRequiredPolicy().budget_required is True
    assert ModelAuditRequiredPolicy().audit_required is True
    assert ModelContextPolicyRequired().context_policy_required is True
