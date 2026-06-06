from tiangong_kernel.l5_plugin_host import PluginManifestView, PluginRegistrySnapshot


def test_l5_phase1_manifest_has_no_loader_handler_or_callable_fields():
    manifest = PluginManifestView(
        plugin_id="plugin:stub",
        name="stub",
        version="0.1.0",
        kind="declaration",
        declared_entry_ref="entry:stub",
    )
    names = set(manifest.__dataclass_fields__)
    for blocked in ("loader", "handler", "module", "function", "class_ref", "command_template", "network_address", "file_write_target"):
        assert blocked not in names


def test_l5_phase1_registry_snapshot_has_no_loader_methods():
    snapshot = PluginRegistrySnapshot(snapshot_ref="registry_snapshot:phase1")
    names = set(dir(snapshot))
    for blocked in ("load", "discover", "scan", "execute", "invoke"):
        assert blocked not in names
