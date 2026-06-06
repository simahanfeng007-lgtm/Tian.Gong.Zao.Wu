from tiangong_kernel.l5_plugin_host import PluginArtifactProductionMountBindingDeclaration, PluginHostGovernanceGateDeclaration


def test_artifact_factory_cannot_bypass_policy_lease_audit():
    p = PluginArtifactProductionMountBindingDeclaration()
    g = PluginHostGovernanceGateDeclaration()
    assert p.required_policy_refs
    assert p.required_approval_ref
    assert g.lease_gate_ref
    assert g.audit_evidence_gate_ref
