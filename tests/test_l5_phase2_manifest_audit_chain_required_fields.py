from l5_phase2_sample_factory import mutable_manifest_namespace, quality_gate


def test_audit_chain_refs_are_required_by_manifest_quality_gate():
    for attr in ("actor_ref", "scope_ref", "trace_ref", "accountability_ref", "tamper_evidence_ref"):
        manifest = mutable_manifest_namespace()
        setattr(manifest, attr, "")
        report = quality_gate().evaluate(manifest)
        assert not report.passed
        assert any(issue.field_path == attr for issue in report.issues)


def test_lifecycle_event_refs_are_declarative_and_required():
    manifest = mutable_manifest_namespace()
    manifest.lifecycle_event_refs = tuple()
    report = quality_gate().evaluate(manifest)
    assert not report.passed
    assert any(issue.field_path == "lifecycle_event_refs" for issue in report.issues)
