from pathlib import Path

def test_test_inventory_compare_blocks_deleted_tests():
    root = Path(__file__).resolve().parents[1] / 'tests'
    phase7 = sorted(p.name for p in root.glob('test_l6_phase7_*.py'))
    assert len(phase7) >= 45
