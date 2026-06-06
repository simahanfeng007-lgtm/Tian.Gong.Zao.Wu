from pathlib import Path


def test_l5_phase8_no_legacy_runtime_capability_package():
    source = Path("tiangong_kernel/l5_plugin_host/phase8_closure.py").read_text(encoding="utf-8")
    assert "AbilityPackage" not in source
    assert "CapabilityPort" not in source
