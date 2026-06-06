from tiangong_kernel.l5_plugin_host import L5FreezeManifest


def test_l5_phase8_hash_compare_tracks_l5_phase1_phase7():
    manifest = L5FreezeManifest()
    assert "hash_compare:l5_phase1_phase7" in manifest.frozen_hash_manifest_refs
