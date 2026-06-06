from tiangong_kernel.l5_plugin_host import PluginDataGovernanceDeclaration


def test_data_governance_declaration_stores_refs_only():
    decl = PluginDataGovernanceDeclaration(
        data_classification_refs=("data_classification:internal",),
        privacy_boundary_refs=("privacy_boundary:l5",),
        consent_refs=("consent:declared",),
        purpose_refs=("purpose:declared",),
        data_lifecycle_refs=("data_lifecycle:declared",),
    )
    assert decl.consent_refs == ("consent:declared",)
    assert decl.purpose_refs == ("purpose:declared",)
