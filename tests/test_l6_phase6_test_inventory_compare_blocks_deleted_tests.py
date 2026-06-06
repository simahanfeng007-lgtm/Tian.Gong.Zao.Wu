from pathlib import Path

def test_test_inventory_compare_blocks_deleted_tests():
    phase5_tests = sorted(Path('tests').glob('test_l6_phase5_*.py'))
    phase6_tests = sorted(Path('tests').glob('test_l6_phase6_*.py'))
    assert len(phase5_tests) >= 40
    assert len(phase6_tests) >= 40
