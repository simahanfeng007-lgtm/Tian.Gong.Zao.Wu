import pytest

from tiangong_kernel.l6_plugins.governance_control import *

def test_public_projection_minimal_disclosure():
    requirement = MinimalDisclosureRequirement()
    assert requirement.allows_summary is True
    assert requirement.allows_digest is True
    assert requirement.allows_full_payload is False
    report = PublicProjectionRedactionReport()
    assert report.complete_payload_public is False
    with pytest.raises(ValueError):
        MinimalDisclosureRequirement(allows_full_payload=True)
