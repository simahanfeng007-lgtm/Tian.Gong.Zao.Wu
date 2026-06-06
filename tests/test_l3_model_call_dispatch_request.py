from tiangong_kernel.l3_orchestration.model_invocation_flow import ModelBudgetCheckRequest, ModelCredentialNeedRef, ModelAuditNeedRef, ModelPolicyCheckRequest, ModelCallDispatchRequest


def test_l3_dispatch_request_has_l5_checks_and_no_live_call():
    providers=("gpt_5_5",)
    req = ModelCallDispatchRequest(
        dispatch_request_ref="dispatch-ref:1",
        intent_ref="intent-ref:1",
        capability_requirement_ref="req-ref:1",
        context_envelope_ref="context-ref:1",
        provider_candidates=providers,
        l5_policy_check_request=ModelPolicyCheckRequest("policy-req:1", "req-ref:1", providers),
        l5_budget_check_request=ModelBudgetCheckRequest("budget-req:1", "req-ref:1", providers),
        l5_credential_need_ref=ModelCredentialNeedRef("cred-need:1", providers),
        l5_audit_need_ref=ModelAuditNeedRef("audit-need:1", providers),
    )
    assert req.no_live_call is True
    assert req.provider_specific_http_body_not_built is True
