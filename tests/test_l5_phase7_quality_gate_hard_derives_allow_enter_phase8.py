from l5_phase7_builders import passing_quality_gate
from tiangong_kernel.l5_plugin_host import PluginPhase7QualityGate, GENERIC_HOST_BLOCK_TOOL_ONLY


def test_quality_gate_allows_when_all_hard_inputs_true():
    q = passing_quality_gate()
    assert q.allow_enter_l5_phase8 is True


def test_quality_gate_blocks_p0_even_if_requested_true():
    q = PluginPhase7QualityGate().decide(decision_ref="decision:block", p0_count=1, generic_plugin_host_precheck_passed=True, generic_plugin_host_precheck_result="PASS_GENERIC_HOST", allow_enter_l5_phase8=True)
    assert q.allow_enter_l5_phase8 is False


def test_quality_gate_blocks_tool_only_precheck():
    q = PluginPhase7QualityGate().decide(decision_ref="decision:tool_only", generic_plugin_host_precheck_passed=False, generic_plugin_host_precheck_result=GENERIC_HOST_BLOCK_TOOL_ONLY)
    assert q.allow_enter_l5_phase8 is False
