from tiangong_kernel.l5_plugin_host.model_capability_invariants import PluginModelCapabilityRequirementOnlyInvariant


def test_l5_plugin_can_only_declare_requirement():
    inv = PluginModelCapabilityRequirementOnlyInvariant(plugin_id="plugin-ref:demo", declared_requirement_refs=("req-ref:1",))
    assert inv.no_model_client is True
    assert inv.no_direct_dispatch is True
