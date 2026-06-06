import pytest

from tiangong_kernel.l6_plugins.governance_control import *

def test_budget_exhaustion_requires_governance_reason():
    projection = BudgetPressureProjection(budget_exhausted=True)
    assert projection.governance_reason_ref
    assert projection.stops_task_by_default is False
    with pytest.raises(ValueError):
        BudgetPressureProjection(stops_task_by_default=True)
