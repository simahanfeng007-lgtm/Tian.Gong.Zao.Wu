from tiangong_kernel.l5_plugin_host import PluginHostBoundaryGateValidator, PluginHostGovernanceGateDeclaration


def test_governance_gate_covers_all_required_gates():
    g = PluginHostGovernanceGateDeclaration()
    assert g.event_gate_ref and g.effect_gate_ref and g.lease_gate_ref
    assert g.audit_evidence_gate_ref and g.resource_budget_gate_ref
    assert g.artifact_provenance_integrity_gate_ref
    report = PluginHostBoundaryGateValidator().check(g, production_mount_enabled=True)
    assert report.p0_count == 0
    assert report.p1_count == 0
