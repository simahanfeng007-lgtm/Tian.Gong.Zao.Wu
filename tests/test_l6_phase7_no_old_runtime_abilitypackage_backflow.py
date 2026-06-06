from pathlib import Path

def test_no_old_runtime_abilitypackage_backflow():
    root = Path(__file__).resolve().parents[1] / 'tiangong_kernel/l6_plugins/adaptive_collaboration'
    source = '\n'.join(p.read_text(encoding='utf-8') for p in root.glob('*.py') if p.name not in {'forbidden_scan.py', 'invariants.py'})
    for token in ('CapabilityPort(', 'AbilityPackagePort(', 'AbilityPackage('):
        assert token not in source
