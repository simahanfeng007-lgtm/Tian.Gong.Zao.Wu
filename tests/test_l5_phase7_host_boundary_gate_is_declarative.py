from tiangong_kernel.l5_plugin_host import PluginHostBoundaryGateDeclaration, has_forbidden_phase7_method


def test_host_boundary_gate_is_declarative():
    gate = PluginHostBoundaryGateDeclaration()
    assert gate.deny_by_default_declared
    assert gate.least_privilege_declared
    assert not has_forbidden_phase7_method(gate)
    assert gate.no_direct_tool_call_ref
