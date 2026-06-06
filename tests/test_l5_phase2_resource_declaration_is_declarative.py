import pytest

from tiangong_kernel.l5_plugin_host import PluginResourceDeclaration


def test_resource_declaration_has_budget_owner_and_does_not_consume_budget():
    decl = PluginResourceDeclaration(
        cost_budget_ref="budget:cost",
        rate_limit_ref="rate:l5",
        quota_ref="quota:l5",
        budget_owner_ref="owner:l5",
        run_budget_scope_ref="scope:run",
        goal_budget_scope_ref="scope:goal",
        actor_budget_scope_ref="scope:actor",
    )
    assert not decl.budget_consumed
    with pytest.raises(ValueError):
        PluginResourceDeclaration(budget_consumed=True)
