from tiangong_kernel.l5_plugin_host import has_live_phase8_locator


def test_l5_phase8_final_forbidden_scan_allows_inert_patterns():
    inert_pattern = "importlib.import_module"
    assert has_live_phase8_locator(inert_pattern) is True
    # The string is allowed as inert test data; it is not executed or imported here.
