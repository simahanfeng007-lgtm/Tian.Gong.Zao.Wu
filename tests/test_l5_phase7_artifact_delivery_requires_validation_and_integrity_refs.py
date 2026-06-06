from tiangong_kernel.l5_plugin_host import PluginArtifactProductionMountBindingDeclaration


def test_artifact_delivery_requires_validation_and_integrity_refs():
    p = PluginArtifactProductionMountBindingDeclaration()
    assert p.artifact_validation_contract_ref
    assert p.artifact_delivery_contract_ref
    assert p.artifact_integrity_ref
    assert p.artifact_provenance_ref
