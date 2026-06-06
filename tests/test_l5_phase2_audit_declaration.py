import pytest

from tiangong_kernel.l5_plugin_host import PluginAuditDeclaration


def test_audit_declaration_is_responsibility_chain_refs_only():
    decl = PluginAuditDeclaration(
        audit_event_kinds=("manifest_declared",),
        replay_policy_ref="replay:declared",
        responsibility_chain_ref="responsibility:declared",
        provenance_policy_ref="provenance:declared",
        evidence_boundary_ref="evidence_boundary:declared",
        audit_retention_policy_ref="audit_retention:declared",
    )
    assert decl.evidence_required
    assert decl.trace_required
    with pytest.raises(ValueError):
        PluginAuditDeclaration(audit_store_written=True)
