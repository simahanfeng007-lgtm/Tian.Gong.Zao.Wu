import pytest

from tiangong_kernel.l6_plugins.cognitive_continuity import *

def test_humanized_refusal_requires_governance_reason():
    hint = HumanizedRefusalStyleHint(governance_reason=GovernanceReasonKind.BUDGET_EXHAUSTED)
    assert hint.style_only is True
    assert hint.refusal_authority is False
    assert hint.synthetic_governance_reason is False
    with pytest.raises(ValueError):
        HumanizedRefusalStyleHint(governance_reason=None)
    with pytest.raises(ValueError):
        HumanizedRefusalStyleHint(refusal_authority=True)
