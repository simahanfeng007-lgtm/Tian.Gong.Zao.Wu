from pathlib import Path


def test_l5_phase8_no_l4_adapter_imports():
    source = Path("tiangong_kernel/l5_plugin_host/phase8_closure.py").read_text(encoding="utf-8")
    assert "l4_action" not in source
    assert "no_live_l4_adapter_call" in source
