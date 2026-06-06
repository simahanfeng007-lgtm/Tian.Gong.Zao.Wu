from tiangong_kernel.l5_plugin_host import PluginArtifactProductionMountBindingDeclaration


def test_product_artifact_factory_capability_is_kind_and_contract_only():
    p = PluginArtifactProductionMountBindingDeclaration()
    assert "ArtifactFactoryCapability" in p.artifact_capability_kind_refs
    assert p.product_spec_contract_ref.startswith("contract:")
    assert p.artifact_build_contract_ref.startswith("contract:")
