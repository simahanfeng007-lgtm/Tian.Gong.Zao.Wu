from pathlib import Path


def test_l5_phase8_no_l6_plugin_implementation():
    source = Path("tiangong_kernel/l5_plugin_host/phase8_closure.py").read_text(encoding="utf-8")
    assert "class MemoryPlugin" not in source
    assert "class ArtifactFactoryPlugin" not in source
