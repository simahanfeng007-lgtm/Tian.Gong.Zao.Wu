import tiangong_kernel.l5_plugin_host as host
from l5_phase2_sample_factory import complete_manifest
from tiangong_kernel.l5_plugin_host import L5PublicExportMap, to_l5_json


def test_phase2_public_exports_are_data_only_names():
    for name in (
        "PluginManifestSchema",
        "PluginManifestQualityGate",
        "PluginCapabilityTokenDeclaration",
        "PluginTrustBoundaryDeclaration",
        "PluginResourceDeclaration",
    ):
        assert name in host.__all__
    for blocked in ("PluginLoader", "PluginRunner", "PluginExecutor", "SandboxRunner", "RegistryWriter"):
        assert blocked not in host.__all__


def test_phase2_serialization_is_deterministic():
    manifest = complete_manifest()
    assert to_l5_json(manifest) == to_l5_json(manifest)
