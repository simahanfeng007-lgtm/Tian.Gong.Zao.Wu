from tests.l5_phase8_factories import passing_quality_gate


def test_l5_phase8_allows_general_l6_only_when_l5_freeze_passed():
    assert passing_quality_gate().allow_enter_l6_general_plugins is True
    assert passing_quality_gate(full_pytest_passed=False).allow_enter_l6_general_plugins is False
