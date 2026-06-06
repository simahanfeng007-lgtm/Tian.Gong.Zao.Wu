import pytest
from tiangong_kernel.l6_plugins.adaptive_collaboration import TestRunRequirement

def test_test_run_requirement_not_test_execution():
    req = TestRunRequirement()
    assert req.runs_tests is False
    with pytest.raises(ValueError):
        TestRunRequirement(runs_tests=True)
