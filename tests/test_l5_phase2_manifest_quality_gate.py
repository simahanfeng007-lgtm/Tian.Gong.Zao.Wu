from l5_phase2_sample_factory import complete_manifest, mutable_manifest_namespace, quality_gate


def test_complete_manifest_passes_quality_gate():
    report = quality_gate().evaluate(complete_manifest())
    assert report.passed
    assert report.issues == ()


def test_missing_plugin_id_blocks_quality_gate():
    manifest = mutable_manifest_namespace()
    manifest.plugin_id = ""
    report = quality_gate().evaluate(manifest)
    assert not report.passed
    assert any(issue.field_path == "plugin_id" for issue in report.issues)


def test_missing_core_declarations_block_quality_gate():
    manifest = mutable_manifest_namespace()
    manifest.permission_decl = None
    manifest.resource_decl = None
    manifest.credential_decl = None
    report = quality_gate().evaluate(manifest)
    fields = {issue.field_path for issue in report.issues}
    assert "permission_decl" in fields
    assert "resource_decl" in fields
    assert "credential_decl" in fields
