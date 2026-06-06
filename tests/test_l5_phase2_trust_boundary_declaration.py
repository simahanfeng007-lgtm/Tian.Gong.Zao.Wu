import pytest

from l5_phase2_sample_factory import mutable_manifest_namespace, quality_gate
from tiangong_kernel.l5_plugin_host import PluginTrustBoundaryDeclaration


def test_trust_boundary_declares_host_plugin_data_and_external_refs():
    decl = PluginTrustBoundaryDeclaration(
        host_boundary_ref="boundary:host",
        plugin_boundary_ref="boundary:plugin",
        data_boundary_refs=("boundary:data",),
        tool_boundary_refs=("boundary:tool",),
        network_boundary_refs=("boundary:network",),
        credential_boundary_refs=("boundary:credential",),
        external_disclosure_boundary_refs=("boundary:external",),
    )
    assert not decl.boundary_decision_executed
    with pytest.raises(ValueError):
        PluginTrustBoundaryDeclaration(boundary_decision_executed=True)


def test_missing_trust_boundary_refs_blocks_manifest():
    manifest = mutable_manifest_namespace()
    manifest.trust_boundary_decl = PluginTrustBoundaryDeclaration()
    report = quality_gate().evaluate(manifest)
    fields = {issue.field_path for issue in report.issues}
    assert "trust_boundary_decl.host_boundary_ref" in fields
    assert "trust_boundary_decl.plugin_boundary_ref" in fields
    assert "trust_boundary_decl.data_boundary_refs" in fields
