from l5_phase2_sample_factory import clone_manifest, complete_manifest
from tiangong_kernel.l5_plugin_host import calculate_manifest_digest, canonical_manifest_payload


def test_manifest_hash_excludes_self_and_signature_reference():
    manifest = complete_manifest()
    changed_self = clone_manifest(manifest_hash="0" * 64)
    changed_signature = clone_manifest(signature_ref=None)
    assert calculate_manifest_digest(manifest) == calculate_manifest_digest(changed_self)
    assert calculate_manifest_digest(manifest) == calculate_manifest_digest(changed_signature)
    payload = canonical_manifest_payload(manifest)
    assert "manifest_hash" not in payload
    assert "signature_ref" not in payload


def test_manifest_hash_field_order_does_not_change_digest():
    first = {"b": 2, "a": 1, "manifest_hash": "x"}
    second = {"manifest_hash": "y", "a": 1, "b": 2}
    assert calculate_manifest_digest(first) == calculate_manifest_digest(second)
