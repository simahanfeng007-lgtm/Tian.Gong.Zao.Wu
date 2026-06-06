from tiangong_kernel.l5_plugin_host.model_capability_invariants import build_plugin_model_access_invariants


def test_l5_scan_detects_raw_model_sdk_import():
    _, sdk_inv, http_inv = build_plugin_model_access_invariants("plugin-ref:bad", "import openai\n", ("req-ref:1",))
    assert sdk_inv.passed is False
    assert http_inv.passed is True
