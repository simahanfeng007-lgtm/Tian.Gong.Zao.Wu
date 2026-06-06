from tiangong_kernel.l5_plugin_host import L5ClosureSummary, L5ClosureValidator


def test_l5_phase8_closure_summary_includes_all_phases():
    closure = L5ClosureSummary()
    assert len(closure.consumed_phase_refs) == 7
    assert closure.consumed_phase_refs[0] == "phase:l5_phase1"
    assert closure.consumed_phase_refs[-1] == "phase:l5_phase7"
    assert L5ClosureValidator().check(closure)
