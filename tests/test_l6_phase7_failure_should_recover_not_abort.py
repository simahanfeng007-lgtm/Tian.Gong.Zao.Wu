from tiangong_kernel.l6_plugins.adaptive_collaboration import LongChainAdaptiveRecoveryPlan

def test_failure_should_recover_not_abort():
    plan = LongChainAdaptiveRecoveryPlan()
    assert plan.aborts_by_default is False
    assert plan.has_low_cost_continuation is True
