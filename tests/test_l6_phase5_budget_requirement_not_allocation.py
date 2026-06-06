import pytest

from tiangong_kernel.l6_plugins.governance_control import *

def test_budget_requirement_not_allocation():
    req = BudgetRequirement()
    assert req.allocation_made is False
    assert req.charge_made is False
    with pytest.raises(ValueError):
        BudgetRequirement(allocation_made=True)
    with pytest.raises(ValueError):
        BudgetRequirement(charge_made=True)
