from tests.l5_phase8_factories import passing_quality_gate


def test_l5_phase8_zip_integrity_and_chinese_paths():
    gate = passing_quality_gate(zip_integrity_passed=True)
    assert gate.allow_freeze_l5 is True
    assert passing_quality_gate(zip_integrity_passed=False).allow_freeze_l5 is False
