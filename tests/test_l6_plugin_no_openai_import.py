from tiangong_kernel.l5_plugin_host.model_capability_invariants import scan_plugin_source_for_raw_model_access


def test_l6_scan_blocks_raw_access_pattern():
    violations = scan_plugin_source_for_raw_model_access('import openai\n')
    assert violations
