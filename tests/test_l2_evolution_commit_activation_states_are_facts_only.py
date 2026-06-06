from __future__ import annotations

from dataclasses import is_dataclass

import pytest

from tiangong_kernel.l0_primitives.identity import RefId, TypedRef
from tiangong_kernel.l2_state.self_evolution_commit_state import (
    EvolutionActivationState,
    EvolutionCommitState,
    EvolutionHotSwitchState,
    EvolutionPostCommitObservationState,
    EvolutionRollbackValidationState,
    EvolutionTombstoneState,
)
from tiangong_kernel.l2_state.state_identity import L2StateIdentity, L2StateKind
from tiangong_kernel.l2_state.state_status import L2StateStatus, L2StateStatusKind


def _ref(suffix: int, ref_type: str = "self_evolution") -> TypedRef:
    return TypedRef(RefId(f"ref:{suffix:032x}"), ref_type)


def _identity(suffix: int) -> L2StateIdentity:
    return L2StateIdentity(_ref(suffix, "l2_state"), L2StateKind.CANDIDATE)


def _status() -> L2StateStatus:
    return L2StateStatus(L2StateStatusKind.DECLARED)


def test_l2_self_evolution_commit_states_are_facts_only() -> None:
    states = (
        EvolutionCommitState(identity=_identity(1), status=_status(), commit_intent_ref=_ref(2)),
        EvolutionActivationState(identity=_identity(3), status=_status(), activation_hint_ref=_ref(4)),
        EvolutionHotSwitchState(identity=_identity(5), status=_status(), rollback_anchor_ref=_ref(6)),
        EvolutionPostCommitObservationState(identity=_identity(7), status=_status(), observation_requirement_refs=(_ref(8),)),
        EvolutionTombstoneState(identity=_identity(9), status=_status(), tombstone_ref=_ref(10)),
        EvolutionRollbackValidationState(identity=_identity(11), status=_status(), rollback_validation_refs=(_ref(12),)),
    )

    for state in states:
        assert is_dataclass(state)
        assert hasattr(state, "__slots__")
        assert state.state_only is True
        assert state.ref_only is True
        assert state.no_patch_apply is True
        assert state.no_auto_merge is True
        assert state.writes_runtime is False

    with pytest.raises(ValueError):
        EvolutionCommitState(identity=_identity(13), status=_status(), no_auto_merge=False)
