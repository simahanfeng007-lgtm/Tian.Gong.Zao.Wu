import pytest

from tiangong_kernel.l6_plugins.cognitive_continuity import *

def test_affective_governance_binding_no_synthetic_reason():
    binding = AffectiveGovernanceBinding(governance_reason=GovernanceReasonKind.TOOL_UNAVAILABLE)
    assert binding.creates_governance_reason is False
    assert binding.bypasses_l5 is False
    with pytest.raises(ValueError):
        AffectiveGovernanceBinding(governance_reason=None)
    with pytest.raises(ValueError):
        AffectiveGovernanceBinding(creates_governance_reason=True)
