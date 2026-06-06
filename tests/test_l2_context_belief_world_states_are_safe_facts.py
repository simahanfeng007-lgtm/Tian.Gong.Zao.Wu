from __future__ import annotations

import pytest

from tiangong_kernel.l0_primitives.identity import RefId, TypedRef
from tiangong_kernel.l2_state.belief_state import BeliefEventPrecedenceState, BeliefHypothesisState
from tiangong_kernel.l2_state.context_safety_state import InstructionTaintState, MemoryInjectionBoundaryState, ToolOutputTaintState
from tiangong_kernel.l2_state.state_identity import L2StateIdentity, L2StateKind
from tiangong_kernel.l2_state.state_status import L2StateStatus, L2StateStatusKind
from tiangong_kernel.l2_state.world_state import WorldSnapshotState, WorldTrustBoundaryState


def _ref(suffix: int, ref_type: str = "context_belief_world") -> TypedRef:
    return TypedRef(RefId(f"ref:{suffix:032x}"), ref_type)


def _identity(suffix: int) -> L2StateIdentity:
    return L2StateIdentity(_ref(suffix, "l2_state"), L2StateKind.MEMORY_CONTEXT)


def _status() -> L2StateStatus:
    return L2StateStatus(L2StateStatusKind.DECLARED)


def test_l2_belief_world_context_safety_states_do_not_execute_or_override() -> None:
    belief = BeliefHypothesisState(identity=_identity(1), status=_status(), belief_ref=_ref(2), evidence_refs=(_ref(3),), event_refs=(_ref(4),), confidence=0.8)
    precedence = BeliefEventPrecedenceState(identity=_identity(5), status=_status(), belief_ref=belief.belief_ref, event_refs=belief.event_refs)
    world = WorldSnapshotState(identity=_identity(6), status=_status(), world_state_ref=_ref(7), evidence_ref=_ref(8), trust_boundary_ref=_ref(9), freshness_score=0.4)
    trust = WorldTrustBoundaryState(identity=_identity(10), status=_status(), world_state_ref=world.world_state_ref, trust_boundary_ref=_ref(11), trust_score=0.6)
    instruction = InstructionTaintState(identity=_identity(12), status=_status(), source_ref=_ref(13))
    tool = ToolOutputTaintState(identity=_identity(14), status=_status(), source_ref=_ref(15))
    memory = MemoryInjectionBoundaryState(identity=_identity(16), status=_status(), memory_refs=(_ref(17),), boundary_status="not_reviewed")

    assert belief.updates_belief is False
    assert belief.overrides_event_fact is False
    assert precedence.event_precedes_belief is True
    assert world.syncs_real_world is False
    assert world.canonical_without_evidence is False
    assert trust.trust_score == 0.6
    assert instruction.system_instruction_eligible is False
    assert tool.untrusted_output is True
    assert memory.injected is False

    with pytest.raises(ValueError):
        BeliefHypothesisState(identity=_identity(18), status=_status(), confidence=1.5)
    with pytest.raises(ValueError):
        InstructionTaintState(identity=_identity(19), status=_status(), system_instruction_eligible=True)
