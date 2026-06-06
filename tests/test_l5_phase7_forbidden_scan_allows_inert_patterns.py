from tiangong_kernel.l5_plugin_host import has_live_phase7_locator


def test_inert_pattern_strings_can_be_checked_without_execution():
    sample = ("importlib.import_module", "call_tool", "build_artifact")
    assert has_live_phase7_locator(sample) is True
    # The strings above are inert test data. They are not imports or calls.
