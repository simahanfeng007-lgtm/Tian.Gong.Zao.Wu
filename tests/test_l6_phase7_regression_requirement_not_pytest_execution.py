import pytest
from tiangong_kernel.l6_plugins.adaptive_collaboration import RegressionValidationRequirement

def test_regression_requirement_not_pytest_execution():
    req = RegressionValidationRequirement()
    assert req.executes_pytest is False
    with pytest.raises(ValueError):
        RegressionValidationRequirement(executes_pytest=True)
