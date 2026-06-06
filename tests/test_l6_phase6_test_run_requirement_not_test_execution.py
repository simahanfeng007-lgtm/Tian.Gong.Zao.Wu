import pytest
from tiangong_kernel.l6_plugins.product_delivery import *

def test_test_run_requirement_not_test_execution():
    req = TestRunRequirement()
    assert req.performs_test_run is False
    with pytest.raises(ValueError):
        TestRunRequirement(performs_test_run=True)
