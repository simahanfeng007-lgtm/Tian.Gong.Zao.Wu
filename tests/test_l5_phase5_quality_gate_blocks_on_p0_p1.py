from l5_phase5_helpers import full_quality_gate, validate_all, valid_isolation


def test_quality_gate_blocks_on_p1():
    report = validate_all(isolation_decls=(valid_isolation(isolation_boundary_ref=""),))
    gate = full_quality_gate(report)
    assert gate.p1_count > 0
    assert gate.allow_enter_l5_phase6 is False


def test_quality_gate_blocks_when_full_pytest_false():
    gate = full_quality_gate(full_pytest_passed=False)
    assert gate.allow_enter_l5_phase6 is False
