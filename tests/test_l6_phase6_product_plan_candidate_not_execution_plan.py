import pytest
from tiangong_kernel.l6_plugins.product_delivery import *

def test_product_plan_candidate_not_execution_plan():
    plan = ProductPlanCandidate()
    assert plan.execution_plan is False
    with pytest.raises(ValueError):
        ProductPlanCandidate(execution_plan=True)
