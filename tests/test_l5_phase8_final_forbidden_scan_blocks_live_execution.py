from tiangong_kernel.l5_plugin_host import has_live_phase8_locator


def test_l5_phase8_final_forbidden_scan_blocks_live_execution():
    assert has_live_phase8_locator("https://example.invalid/build_artifact") is True
