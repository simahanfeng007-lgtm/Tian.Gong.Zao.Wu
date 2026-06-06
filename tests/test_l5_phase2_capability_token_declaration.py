import pytest

from l5_phase2_sample_factory import mutable_manifest_namespace, quality_gate
from tiangong_kernel.l5_plugin_host import PluginCapabilityTokenDeclaration


def test_capability_token_declares_scope_lease_expiry_and_revocation():
    decl = PluginCapabilityTokenDeclaration(
        required_token_refs=("capability_token:declared",),
        token_scope_refs=("scope:capability",),
        lease_ref="lease:capability",
        expiry_ref="expiry:capability",
        revocation_check_ref="revocation:capability",
    )
    assert not decl.token_issued
    with pytest.raises(ValueError):
        PluginCapabilityTokenDeclaration(token_issued=True)


def test_capability_token_missing_constraints_blocks_manifest():
    manifest = mutable_manifest_namespace()
    manifest.capability_token_decl = PluginCapabilityTokenDeclaration(required_token_refs=("capability_token:declared",))
    report = quality_gate().evaluate(manifest)
    fields = {issue.field_path for issue in report.issues}
    assert "capability_token_decl.token_scope_refs" in fields
    assert "capability_token_decl.lease_ref" in fields
    assert "capability_token_decl.expiry_ref" in fields
    assert "capability_token_decl.revocation_check_ref" in fields
