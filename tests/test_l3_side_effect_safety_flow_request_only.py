import pytest

from tiangong_kernel.l3_orchestration import (
    ActionToEffectSafetyFlow,
    AuditEvidenceRequirementFlow,
    EffectAuthorizationFlow,
    LeaseApprovalFlow,
    SecretPrivacyGuardFlow,
    SideEffectExecutionReadinessFlow,
    TransactionCompensationFlow,
)


def test_l3_side_effect_safety_flows_are_request_only_refs():
    for cls in (
        ActionToEffectSafetyFlow,
        AuditEvidenceRequirementFlow,
        EffectAuthorizationFlow,
        LeaseApprovalFlow,
        SecretPrivacyGuardFlow,
        SideEffectExecutionReadinessFlow,
        TransactionCompensationFlow,
    ):
        flow = cls()
        assert flow.request_only is True
        assert flow.advisory_only is True
        assert flow.ref_only is True
        assert flow.no_execution is True
        assert flow.no_decision is True
        assert flow.no_persistence is True

    with pytest.raises(ValueError):
        EffectAuthorizationFlow(grants_permission=True)
    with pytest.raises(ValueError):
        LeaseApprovalFlow(lease_granted=True)
    with pytest.raises(ValueError):
        SecretPrivacyGuardFlow(plain_secret_visible=True)
    with pytest.raises(ValueError):
        TransactionCompensationFlow(commit_performed=True)
    with pytest.raises(ValueError):
        AuditEvidenceRequirementFlow(audit_write_performed=True)
    with pytest.raises(ValueError):
        SideEffectExecutionReadinessFlow(dispatch_enabled=True)
