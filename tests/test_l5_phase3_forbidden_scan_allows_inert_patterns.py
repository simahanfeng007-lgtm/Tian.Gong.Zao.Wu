from tiangong_kernel.l5_plugin_host import PluginRegistryConflictRuleSet


def test_inert_pattern_catalog_is_data_only():
    rule_set = PluginRegistryConflictRuleSet(rule_set_ref="rule_set:test")
    assert "importlib.import_module" in rule_set.live_action_patterns
    assert "subprocess" in rule_set.live_action_patterns
    assert not hasattr(rule_set, "scan_filesystem")
