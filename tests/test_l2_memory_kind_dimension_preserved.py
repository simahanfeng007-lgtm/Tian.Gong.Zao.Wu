from __future__ import annotations

import pytest

from tiangong_kernel.l0_primitives.identity import RefId, TypedRef
from tiangong_kernel.l2_state.memory_state import MemoryCognitiveKind, MemoryRefState
from tiangong_kernel.l2_state.state_identity import L2StateIdentity, L2StateKind
from tiangong_kernel.l2_state.state_status import L2StateStatus, L2StateStatusKind


def _ref(suffix: int, ref_type: str = "memory_ref") -> TypedRef:
    return TypedRef(RefId(f"ref:{suffix:032x}"), ref_type)


def test_l2_memory_kind_dimension_preserves_cognitive_categories() -> None:
    identity = L2StateIdentity(_ref(1, "l2_state"), L2StateKind.MEMORY_CONTEXT)
    status = L2StateStatus(L2StateStatusKind.DECLARED)

    for kind in (
        MemoryCognitiveKind.WORKING,
        MemoryCognitiveKind.EPISODIC,
        MemoryCognitiveKind.SEMANTIC,
        MemoryCognitiveKind.PROCEDURAL,
        MemoryCognitiveKind.SELF,
        MemoryCognitiveKind.SYSTEM,
    ):
        state = MemoryRefState(identity=identity, status=status, memory_ref_id=_ref(2), memory_kind=kind.value)
        assert state.memory_kind == kind.value

    with pytest.raises(ValueError):
        MemoryRefState(identity=identity, status=status, memory_kind="long_term_database")
