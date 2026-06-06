import pytest

from tiangong_kernel.l6_plugins.governance_control import *

def test_privacy_requirement_not_data_access():
    proj = PrivacyRiskProjection()
    assert proj.data_access_granted is False
    assert proj.minimal_summary_only is True
    assert RedactionRequirement().redaction_executed is False
    with pytest.raises(ValueError):
        PrivacyRiskProjection(data_access_granted=True)
