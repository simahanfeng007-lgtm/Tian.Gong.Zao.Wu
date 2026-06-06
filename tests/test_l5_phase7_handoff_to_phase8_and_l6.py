from tiangong_kernel.l5_plugin_host import (
    PluginArtifactProductionMountBindingDeclaration,
    PluginHostBoundaryGateDeclaration,
    PluginL6EntryDeclaration,
)


def test_phase7_handoff_to_phase8_and_l6_objects_exist_without_execution():
    assert PluginHostBoundaryGateDeclaration().host_boundary_gate_ref
    assert PluginL6EntryDeclaration().entry_contract_ref
    assert PluginArtifactProductionMountBindingDeclaration().artifact_provenance_ref
