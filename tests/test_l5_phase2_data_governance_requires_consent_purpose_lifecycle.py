from l5_phase2_sample_factory import mutable_manifest_namespace, quality_gate
from tiangong_kernel.l5_plugin_host import PluginDataGovernanceDeclaration


def test_data_governance_missing_consent_purpose_lifecycle_blocks_manifest():
    manifest = mutable_manifest_namespace()
    manifest.data_governance_decl = PluginDataGovernanceDeclaration()
    report = quality_gate().evaluate(manifest)
    fields = {issue.field_path for issue in report.issues}
    assert "data_governance_decl.consent_refs" in fields
    assert "data_governance_decl.purpose_refs" in fields
    assert "data_governance_decl.data_lifecycle_refs" in fields


def test_manifest_top_level_consent_purpose_lifecycle_are_required():
    for attr in ("consent_refs", "purpose_refs", "data_lifecycle_refs"):
        manifest = mutable_manifest_namespace()
        setattr(manifest, attr, tuple())
        report = quality_gate().evaluate(manifest)
        assert not report.passed
        assert any(issue.field_path == attr for issue in report.issues)
