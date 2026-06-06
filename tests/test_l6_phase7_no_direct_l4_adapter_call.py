from pathlib import Path

def test_no_direct_l4_adapter_call():
    root = Path(__file__).resolve().parents[1] / 'tiangong_kernel/l6_plugins/adaptive_collaboration'
    source = '\n'.join(p.read_text(encoding='utf-8') for p in root.glob('*.py'))
    assert 'l4_adapter.' not in source
