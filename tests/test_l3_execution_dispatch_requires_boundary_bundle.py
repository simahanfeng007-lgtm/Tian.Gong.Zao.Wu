from tiangong_kernel.l3_orchestration import (
    NoExecutionDispatchWithoutSafetyChainInvariant,
    SideEffectDispatchRequiresAuditRequirementInvariant,
    SideEffectDispatchRequiresBoundaryBundleInvariant,
    SideEffectDispatchRequiresLeaseOrDenialInvariant,
    SideEffectDispatchRequiresSecretPrivacyGuardInvariant,
    SideEffectDispatchRequiresTransactionCompensationPlanInvariant,
)


def test_l3_side_effect_dispatch_invariants_are_requirement_only():
    invariants = (
        SideEffectDispatchRequiresBoundaryBundleInvariant(),
        SideEffectDispatchRequiresAuditRequirementInvariant(),
        SideEffectDispatchRequiresLeaseOrDenialInvariant(),
        SideEffectDispatchRequiresSecretPrivacyGuardInvariant(),
        SideEffectDispatchRequiresTransactionCompensationPlanInvariant(),
        NoExecutionDispatchWithoutSafetyChainInvariant(),
    )
    for invariant in invariants:
        assert invariant.invariant_only is True
    assert NoExecutionDispatchWithoutSafetyChainInvariant().l3_dispatch_enabled is False
