from l5_phase2_sample_factory import clone_manifest, complete_manifest
from tiangong_kernel.l5_plugin_host import calculate_manifest_digest


def test_manifest_hash_is_stable_for_same_payload():
    manifest = complete_manifest()
    assert calculate_manifest_digest(manifest) == calculate_manifest_digest(manifest)
    assert manifest.manifest_hash == calculate_manifest_digest(manifest)


def test_manifest_hash_changes_when_included_field_changes():
    manifest = complete_manifest()
    changed = clone_manifest(producer_ref="producer:l5_engineer_changed")
    assert calculate_manifest_digest(manifest) != calculate_manifest_digest(changed)
