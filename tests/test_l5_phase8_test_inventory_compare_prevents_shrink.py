from tests.l5_phase8_factories import passing_quality_gate


def test_l5_phase8_test_inventory_compare_prevents_shrink():
    assert passing_quality_gate(test_inventory_compare_passed=True).allow_freeze_l5 is True
    assert passing_quality_gate(test_inventory_compare_passed=False).allow_freeze_l5 is False
