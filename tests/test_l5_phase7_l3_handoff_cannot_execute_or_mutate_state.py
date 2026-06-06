from tiangong_kernel.l5_plugin_host import PluginHostBoundaryGateValidator, PluginL3HandoffDeclaration


def test_l3_handoff_has_no_execution_plan_or_state_mutation():
    h = PluginL3HandoffDeclaration()
    assert h.no_direct_execution_plan_ref
    assert h.no_runtime_state_mutation_ref
    report = PluginHostBoundaryGateValidator().check(h)
    assert report.p0_count == 0
