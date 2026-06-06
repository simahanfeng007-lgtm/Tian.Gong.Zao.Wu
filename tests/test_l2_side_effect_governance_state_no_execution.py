from dataclasses import FrozenInstanceError, is_dataclass

import pytest

from l3_phase1_builders import typed
from tiangong_kernel.l2_state import (
    ApprovalState,
    DataGovernanceState,
    L2StateIdentity,
    L2StateKind,
    L2StateStatus,
    PolicyBindingState,
    PrivacyGuardState,
    SecretExposureGuardState,
    SideEffectGovernanceChainState,
)


def identity(index: int) -> L2StateIdentity:
    return L2StateIdentity(state_ref=typed(index, "side_effect_state"), kind=L2StateKind.BOUNDARY)


def test_l2_side_effect_governance_states_are_state_only():
    states = (
        SideEffectGovernanceChainState(identity(1), L2StateStatus(), action_intent_ref=typed(2, "action_intent")),
        PolicyBindingState(identity(3), L2StateStatus()),
        ApprovalState(identity(4), L2StateStatus()),
        DataGovernanceState(identity(5), L2StateStatus()),
        SecretExposureGuardState(identity(6), L2StateStatus()),
        PrivacyGuardState(identity(7), L2StateStatus()),
    )
    for state in states:
        assert is_dataclass(state)
        assert hasattr(type(state), "__slots__")
        with pytest.raises(FrozenInstanceError):
            state.schema_version = "changed"
        assert state.state_only is True

    assert ApprovalState(identity(8), L2StateStatus()).issues_ticket is False
    assert SecretExposureGuardState(identity(9), L2StateStatus()).plain_secret_visible is False
    assert PrivacyGuardState(identity(10), L2StateStatus()).external_disclosure_authorized is False
