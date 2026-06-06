from pathlib import Path


def test_phase3_test_inventory_has_not_removed_existing_l5_phase2_tests():
    phase2_tests = sorted(Path("tests").glob("test_l5_phase2_*.py"))
    phase3_tests = sorted(Path("tests").glob("test_l5_phase3_*.py"))
    assert len(phase2_tests) >= 30
    assert len(phase3_tests) >= 40
