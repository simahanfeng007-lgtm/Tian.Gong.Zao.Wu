import tiangong_kernel.l5_plugin_host as host
from tiangong_kernel.l5_plugin_host import L5PublicExportMap, PluginHostIdentity, to_l5_json, to_l5_primitive


def test_public_exports_are_explicit_and_safe_data_shells():
    assert "PluginManifestView" in host.__all__
    assert "PluginRegistrySnapshot" in host.__all__
    assert "PluginHostIdentity" in host.__all__
    export_map = L5PublicExportMap(
        export_map_ref="export_map:phase1",
        safe_exports=tuple(host.__all__),
        blocked_exports=("plugin_loader", "live_action_adapter"),
    )
    assert "PluginManifestView" in export_map.safe_exports


def test_serialization_is_deterministic_and_utf8_safe():
    identity = PluginHostIdentity(host_ref="host:凌霜")
    first = to_l5_json(identity)
    second = to_l5_json(identity)
    assert first == second
    assert "凌霜" in first
    primitive = to_l5_primitive(identity)
    assert primitive["host_ref"] == "host:凌霜"
