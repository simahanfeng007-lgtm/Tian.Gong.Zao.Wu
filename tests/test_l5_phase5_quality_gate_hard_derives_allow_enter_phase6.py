from l5_phase5_helpers import full_quality_gate


def test_quality_gate_cannot_be_forced_true_when_inputs_fail():
    gate = full_quality_gate(full_pytest_passed=False)
    assert gate.allow_enter_l5_phase6 is False


def test_quality_gate_all_true_allows_phase6():
    gate = full_quality_gate()
    assert gate.allow_enter_l5_phase6 is True
