from tiangong_kernel.l5_plugin_host import has_live_phase7_locator


def test_forbidden_scan_blocks_live_l3_l4_l6_artifact_actions():
    assert has_live_phase7_locator(("https://external.invalid",))
    assert has_live_phase7_locator(("build_artifact now",))
    assert has_live_phase7_locator(("importlib.import_module",))
