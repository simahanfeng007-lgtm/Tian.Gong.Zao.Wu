import pytest

from tiangong_kernel.l6_plugins.cognitive_continuity import *

def test_long_term_affective_drift_report_only():
    monitor = LongTermAffectiveDriftMonitor(drift_score=0.4)
    assert monitor.report_only is True
    assert monitor.mutates_core_policy is False
    with pytest.raises(ValueError):
        LongTermAffectiveDriftMonitor(mutates_core_policy=True)
