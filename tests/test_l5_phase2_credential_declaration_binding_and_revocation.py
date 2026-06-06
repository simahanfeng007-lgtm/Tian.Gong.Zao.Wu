from l5_phase2_sample_factory import mutable_manifest_namespace, quality_gate
from tiangong_kernel.l5_plugin_host import PluginCredentialDeclaration


def test_credential_missing_handle_purpose_lease_revocation_blocks_manifest():
    manifest = mutable_manifest_namespace()
    manifest.credential_decl = PluginCredentialDeclaration()
    report = quality_gate().evaluate(manifest)
    fields = {issue.field_path for issue in report.issues}
    assert "credential_decl.credential_handle_refs" in fields
    assert "credential_decl.credential_purpose_refs" in fields
    assert "credential_decl.credential_lease_ref" in fields
    assert "credential_decl.credential_revocation_ref" in fields


def test_credential_value_absent_and_redacted_are_enforced_at_object_level():
    try:
        PluginCredentialDeclaration(value_absent_required=False)
    except ValueError as exc:
        assert "absent" in str(exc)
    else:
        raise AssertionError("credential declaration accepted absent=false")
