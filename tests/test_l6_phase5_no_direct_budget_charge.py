import pytest

from tiangong_kernel.l6_plugins.governance_control import *

def test_no_direct_budget_charge_declared():
    assert BudgetPressureProjection().stops_task_by_default is False
    with pytest.raises(ValueError):
        GovernanceControlPluginDeclaration(plugin_ref='l6_phase5:bad_budget', plugin_kind=GovernancePluginKind.BUDGET_PRESSURE, summary='bad', allocates_budget=True)
