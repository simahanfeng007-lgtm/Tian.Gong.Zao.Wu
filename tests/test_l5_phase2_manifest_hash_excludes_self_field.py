from l5_phase2_sample_factory import clone_manifest, complete_manifest
from tiangong_kernel.l5_plugin_host import calculate_manifest_digest


def test_manifest_hash_does_not_recurse_on_self_field():
    manifest = complete_manifest()
    a = clone_manifest(manifest_hash="a" * 64)
    b = clone_manifest(manifest_hash="b" * 64)
    assert calculate_manifest_digest(a) == calculate_manifest_digest(b)
