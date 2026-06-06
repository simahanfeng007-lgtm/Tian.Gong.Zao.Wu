from l5_phase2_sample_factory import mutable_manifest_namespace, quality_gate


def test_missing_capability_token_trust_boundary_and_privacy_refs_block_manifest():
    manifest = mutable_manifest_namespace()
    manifest.capability_token_decl = None
    manifest.trust_boundary_decl = None
    manifest.consent_refs = tuple()
    manifest.purpose_refs = tuple()
    manifest.data_lifecycle_refs = tuple()
    report = quality_gate().evaluate(manifest)
    fields = {issue.field_path for issue in report.issues}
    assert "capability_token_decl" in fields
    assert "trust_boundary_decl" in fields
    assert "consent_refs" in fields
    assert "purpose_refs" in fields
    assert "data_lifecycle_refs" in fields
