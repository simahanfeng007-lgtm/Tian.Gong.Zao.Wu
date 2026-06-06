import pytest

from tiangong_kernel.l6_plugins.governance_control import *

def test_human_gate_not_confirmation_ticket():
    gate = HumanGateRequirement()
    assert gate.confirmation_ticket_issued is False
    assert gate.user_confirmation_claimed is False
    assert HumanConfirmationPromptHint().ticket_issued is False
    with pytest.raises(ValueError):
        HumanGateRequirement(confirmation_ticket_issued=True)
