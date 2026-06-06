from pathlib import Path


def test_l5_model_capability_patch_has_no_network_model_call():
    source = Path("tiangong_kernel/l5_plugin_host/model_capability_invariants.py").read_text(encoding="utf-8")
    assert "requests." not in source and "httpx." not in source and "urllib.request" not in source
