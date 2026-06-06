from tiangong_kernel.l5_plugin_host import GENERIC_HOST_BLOCK_TOOL_ONLY, GENERIC_HOST_PASS, GENERIC_HOST_PASS_WITH_COMPATIBLE_EXTENSION, PluginGenericHostPrecheckValidator


def test_generic_plugin_host_precheck_passes_generic_host():
    report = PluginGenericHostPrecheckValidator().check(supports_plugin_kind=True, supports_capability_kind=True, supports_mount_kind=True, supports_contract_ref=True)
    assert report.result == GENERIC_HOST_PASS
    assert report.precheck_digest


def test_generic_plugin_host_precheck_allows_compatible_extension():
    report = PluginGenericHostPrecheckValidator().check(supports_plugin_kind=True, supports_capability_kind=False, supports_mount_kind=True, supports_contract_ref=True)
    assert report.result == GENERIC_HOST_PASS_WITH_COMPATIBLE_EXTENSION


def test_generic_plugin_host_precheck_blocks_tool_schema_only():
    report = PluginGenericHostPrecheckValidator().check(supports_plugin_kind=False, supports_capability_kind=False, supports_mount_kind=False, supports_contract_ref=False, tool_schema_only=True)
    assert report.result == GENERIC_HOST_BLOCK_TOOL_ONLY
