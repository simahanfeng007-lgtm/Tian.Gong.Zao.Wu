from tiangong_kernel.l5_plugin_host import L5FreezeManifest, L5FreezeManifestValidator


def test_l5_phase8_freeze_manifest_includes_public_exports():
    manifest = L5FreezeManifest()
    assert manifest.frozen_public_export_refs
    assert manifest.frozen_quality_gate_refs
    assert manifest.frozen_handoff_refs
    assert L5FreezeManifestValidator().check(manifest)
