from __future__ import annotations

from dataclasses import is_dataclass

import pytest

from tiangong_kernel.l0_primitives.identity import RefId, TypedRef
from tiangong_kernel.l2_state.memory_forgetting_state import (
    MemoryDecayState,
    MemoryDeletionLinkState,
    MemoryGovernanceState,
    MemoryInterferenceState,
    MemoryPrivacyBoundaryState,
    MemoryPruningState,
    MemoryRetentionState,
    MemoryRevisionState,
    MemorySuppressionState,
)
from tiangong_kernel.l2_state.state_identity import L2StateIdentity, L2StateKind
from tiangong_kernel.l2_state.state_status import L2StateStatus, L2StateStatusKind


def _ref(suffix: int, ref_type: str = "memory_ref") -> TypedRef:
    return TypedRef(RefId(f"ref:{suffix:032x}"), ref_type)


def _identity(suffix: int) -> L2StateIdentity:
    return L2StateIdentity(_ref(suffix, "l2_state"), L2StateKind.MEMORY_CONTEXT)


def _status() -> L2StateStatus:
    return L2StateStatus(L2StateStatusKind.DECLARED)


def test_l2_memory_forgetting_states_are_frozen_slots_and_ref_only() -> None:
    states = (
        MemoryGovernanceState(identity=_identity(1), status=_status(), memory_refs=(_ref(2),)),
        MemoryRetentionState(identity=_identity(3), status=_status(), retention_score=0.5),
        MemoryDecayState(identity=_identity(4), status=_status(), decay_score=0.2),
        MemoryInterferenceState(identity=_identity(5), status=_status(), interference_score=0.3),
        MemorySuppressionState(identity=_identity(6), status=_status(), suppression_ref=_ref(7)),
        MemoryPruningState(identity=_identity(8), status=_status(), pruning_candidate_count=1),
        MemoryRevisionState(identity=_identity(9), status=_status(), revision_ref=_ref(10)),
        MemoryDeletionLinkState(identity=_identity(11), status=_status(), deletion_ref=_ref(12), tombstone_ref=_ref(13)),
        MemoryPrivacyBoundaryState(identity=_identity(14), status=_status(), privacy_ref=_ref(15)),
    )

    for state in states:
        assert is_dataclass(state)
        assert hasattr(state, "__slots__")
        assert state.state_only is True
        assert state.ref_only is True
        assert state.no_memory_read is True
        assert state.no_context_write is True
        assert state.executes_forgetting is False
        assert state.deletes_memory is False

    with pytest.raises(ValueError):
        MemoryDecayState(identity=_identity(16), status=_status(), decay_score=1.2)
