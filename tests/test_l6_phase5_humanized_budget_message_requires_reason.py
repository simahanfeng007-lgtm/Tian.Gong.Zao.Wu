import pytest

from tiangong_kernel.l6_plugins.governance_control import *

def test_humanized_budget_message_requires_reason():
    hint = HumanizedBudgetExhaustionStyleHint()
    assert hint.governance_reason_ref
    assert hint.affective_reason_only is False
    assert hint.refusal_generated is False
    with pytest.raises(ValueError):
        HumanizedBudgetExhaustionStyleHint(affective_reason_only=True)
