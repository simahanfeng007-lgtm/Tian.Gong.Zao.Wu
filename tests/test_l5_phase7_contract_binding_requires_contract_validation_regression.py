from tiangong_kernel.l5_plugin_host import PluginContractBindingDeclaration


def test_contract_binding_has_contract_validation_regression():
    c = PluginContractBindingDeclaration()
    assert c.contract_ref
    assert c.validation_ref
    assert c.regression_ref
    assert c.contract_binding_digest
