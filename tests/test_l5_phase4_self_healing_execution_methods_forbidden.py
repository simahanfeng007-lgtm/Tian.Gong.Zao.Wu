from tiangong_kernel.l5_plugin_host import PluginRecoveryPlanDeclaration, PluginSelfHealingDeclaration, has_forbidden_method


def test_self_healing_and_recovery_plan_have_no_execution_methods():
    assert has_forbidden_method(PluginSelfHealingDeclaration) == ()
    assert has_forbidden_method(PluginRecoveryPlanDeclaration) == ()
