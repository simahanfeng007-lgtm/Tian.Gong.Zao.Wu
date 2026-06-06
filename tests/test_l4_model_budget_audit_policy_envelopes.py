from tiangong_kernel.l4_action_grounding.model_provider_adapter import ModelProviderBudgetEnvelope, ModelProviderAuditEnvelope, ModelProviderPolicyEnvelope


def test_l4_budget_audit_policy_are_refs_only():
    assert ModelProviderBudgetEnvelope("budget-ref:1", "gpt_5_5").does_not_decide_budget is True
    assert ModelProviderAuditEnvelope("audit-ref:1", "gpt_5_5").does_not_write_audit is True
    assert ModelProviderPolicyEnvelope("policy-ref:1", "gpt_5_5").does_not_decide_policy is True
