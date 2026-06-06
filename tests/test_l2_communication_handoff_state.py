from dataclasses import FrozenInstanceError, is_dataclass

import pytest

from tiangong_kernel.l0_primitives.identity import RefId, TypedRef
from tiangong_kernel.l2_state.communication_handoff_state import (
    ActorCollaborationState,
    ActorResultReturnState,
    CommunicationEnvelopeState,
    HandoffAckState,
    HandoffFailureReturnState,
    HandoffNackState,
    HandoffResponsibilityState,
    HandoffResultReturnState,
)
from tiangong_kernel.l2_state.state_identity import L2StateIdentity, L2StateKind
from tiangong_kernel.l2_state.state_status import L2StateStatus, L2StateStatusKind


def _ref(num: int, ref_type: str = "ref") -> TypedRef:
    return TypedRef(RefId(f"ref:{num:032x}"), ref_type)


def _identity(num: int, kind: L2StateKind = L2StateKind.BASE) -> L2StateIdentity:
    return L2StateIdentity(_ref(num, "state"), kind=kind)


def _status() -> L2StateStatus:
    return L2StateStatus(L2StateStatusKind.DECLARED, evidence_refs=(_ref(99, "evidence"),))


def test_l2_communication_envelope_state_tracks_message_chain_refs():
    state = CommunicationEnvelopeState(
        _identity(1),
        _status(),
        _ref(2, "message_envelope"),
        sender_ref=_ref(3, "actor"),
        receiver_ref=_ref(4, "actor"),
        channel_ref=_ref(5, "channel"),
        protocol_ref=_ref(6, "protocol"),
        conversation_ref=_ref(7, "conversation"),
        evidence_refs=(_ref(8, "evidence"),),
    )
    assert is_dataclass(state)
    assert hasattr(type(state), "__slots__")
    assert state.message_envelope_ref.ref_type == "message_envelope"
    assert state.channel_ref and state.channel_ref.ref_type == "channel"
    with pytest.raises(FrozenInstanceError):
        state.schema_version = "changed"


def test_l2_handoff_responsibility_state_tracks_ack_nack_and_result_returns():
    state = HandoffResponsibilityState(
        _identity(10),
        _status(),
        _ref(11, "handoff"),
        from_actor_ref=_ref(12, "actor"),
        to_actor_ref=_ref(13, "actor"),
        ack_ref=_ref(14, "ack"),
        nack_ref=_ref(15, "nack"),
        result_return_ref=_ref(16, "result_return"),
        failure_return_ref=_ref(17, "failure_return"),
    )
    assert state.ack_ref and state.ack_ref.ref_type == "ack"
    assert state.nack_ref and state.nack_ref.ref_type == "nack"
    assert state.result_return_ref and state.result_return_ref.ref_type == "result_return"
    assert state.failure_return_ref and state.failure_return_ref.ref_type == "failure_return"
    assert HandoffAckState is HandoffResponsibilityState
    assert HandoffNackState is HandoffResponsibilityState
    assert HandoffResultReturnState is HandoffResponsibilityState
    assert HandoffFailureReturnState is HandoffResponsibilityState
    assert ActorResultReturnState is HandoffResponsibilityState


def test_l2_actor_collaboration_state_tracks_participants_leases_and_visible_context():
    state = ActorCollaborationState(
        _identity(20),
        _status(),
        _ref(21, "collaboration"),
        participant_refs=(_ref(22, "actor"), _ref(23, "actor")),
        parent_actor_ref=_ref(24, "actor"),
        tool_lease_refs=(_ref(25, "lease"),),
        visible_context_refs=(_ref(26, "context"),),
    )
    assert len(state.participant_refs) == 2
    assert state.tool_lease_refs
    assert state.visible_context_refs
