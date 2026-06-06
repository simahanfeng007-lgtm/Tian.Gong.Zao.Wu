from tiangong_kernel.l5_plugin_host.registry_conflict_rules import PluginRegistryConflictRuleSet


def test_inert_pattern_catalog_can_contain_dangerous_words_without_execution():
    rules = PluginRegistryConflictRuleSet("rule_set:test")
    catalog_text = " ".join(rules.live_action_patterns)
    assert "importlib.import_module" in catalog_text
    assert "subprocess" in catalog_text
    assert not hasattr(rules, "import_module")
