import pytest
from tiangong_kernel.l6_plugins.product_delivery import *

def test_execution_first_with_hard_boundaries():
    policy = ProductExecutionFirstPolicy()
    assert policy.hard_boundaries_preserved is True
    assert policy.bypasses_l5 is False
    with pytest.raises(ValueError):
        ProductExecutionFirstPolicy(bypasses_l5=True)
