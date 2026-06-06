import pytest

from tiangong_kernel.l5_plugin_host import PluginResourceDeclaration


def test_resource_declaration_rejects_unbounded_resource_words():
    with pytest.raises(ValueError):
        PluginResourceDeclaration(cost_budget_ref="budget:unlimited")
    with pytest.raises(ValueError):
        PluginResourceDeclaration(rate_limit_ref="rate:no_limit")
