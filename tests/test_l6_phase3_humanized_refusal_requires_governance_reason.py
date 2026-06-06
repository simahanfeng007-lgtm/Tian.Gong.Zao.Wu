import pytest

from tiangong_kernel.l6_plugins.mind import *


def test_humanized_refusal_style_is_expression_only_and_requires_reason():
    hint = HumanizedRefusalStyleHint(governance_reason=GovernanceRefusalReason.BUDGET_EXHAUSTED)
    assert hint.style_only is True
    assert hint.refusal_authority is False
    with pytest.raises(ValueError):
        HumanizedRefusalStyleHint(governance_reason=None)
    with pytest.raises(ValueError):
        HumanizedRefusalStyleHint(refusal_authority=True)
