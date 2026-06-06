from tiangong_kernel.l5_plugin_host import PluginRegistryValidator


def test_registry_validator_exposes_no_filesystem_scan_methods():
    names = set(dir(PluginRegistryValidator(validator_ref="validator:test")))
    for forbidden in ("scan_filesystem", "walk", "rglob", "read_package", "discover_plugins"):
        assert forbidden not in names
