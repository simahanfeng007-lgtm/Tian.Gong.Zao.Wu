from tiangong_kernel.l6_plugins.adaptive_collaboration import TestRunRequirement

def test_no_direct_test_execution():
    assert TestRunRequirement().runs_tests is False
