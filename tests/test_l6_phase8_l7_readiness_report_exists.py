import pytest
from tiangong_kernel.l6_plugins.final_closure import L7ReadinessReport

def test_l7_readiness_report_exists():
    report = L7ReadinessReport()
    assert report.planning_allowed is True
    assert report.implementation_freeze_allowed is False
    with pytest.raises(ValueError):
        L7ReadinessReport(implementation_freeze_allowed=True)
