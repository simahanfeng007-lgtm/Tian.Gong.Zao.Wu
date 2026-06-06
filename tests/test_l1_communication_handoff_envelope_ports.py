from abc import ABC
from dataclasses import FrozenInstanceError, is_dataclass

import pytest

from tiangong_kernel.l0_primitives.identity import RefId, TypedRef
from tiangong_kernel.l1_ports.communication_handoff_envelope_ports import (
    ActorCommunicationRequest,
    ActorCommunicationResponse,
    ActorHandoffPort,
    HandoffEnvelopeSubmitRequest,
    HandoffEnvelopeSubmitResponse,
    MessageEnvelopePort,
    MessageEnvelopeSubmitRequest,
    MessageEnvelopeSubmitResponse,
    MultiActorCommunicationPort,
)


def _ref(num: int, ref_type: str = "ref") -> TypedRef:
    return TypedRef(RefId(f"ref:{num:032x}"), ref_type)


def test_l1_communication_handoff_ports_are_abstract_protocols():
    for port_cls in (MessageEnvelopePort, ActorHandoffPort, MultiActorCommunicationPort):
        assert issubclass(port_cls, ABC)
        with pytest.raises(TypeError):
            port_cls()


def test_l1_communication_handoff_requests_are_frozen_slots():
    objects = (
        MessageEnvelopeSubmitRequest(_ref(1), _ref(2, "message_envelope"), _ref(3, "actor"), _ref(4, "actor")),
        MessageEnvelopeSubmitResponse(_ref(5), _ref(6, "message_envelope")),
        HandoffEnvelopeSubmitRequest(_ref(7), _ref(8, "handoff"), _ref(9, "message_envelope"), _ref(10, "actor"), _ref(11, "actor"), _ref(12, "conversation")),
        HandoffEnvelopeSubmitResponse(_ref(13), _ref(14, "handoff"), receipt_ref=_ref(15, "receipt")),
        ActorCommunicationRequest(_ref(16), _ref(17, "actor"), _ref(18, "actor"), _ref(19, "message_envelope")),
        ActorCommunicationResponse(_ref(20), _ref(21, "message_envelope")),
    )
    for item in objects:
        assert is_dataclass(item)
        assert hasattr(type(item), "__slots__")
        with pytest.raises(FrozenInstanceError):
            item.schema_version = "changed"


def test_l1_handoff_envelope_submit_request_requires_message_and_actor_chain():
    request = HandoffEnvelopeSubmitRequest(
        _ref(30),
        _ref(31, "handoff"),
        _ref(32, "message_envelope"),
        _ref(33, "actor"),
        _ref(34, "actor"),
        _ref(35, "conversation"),
        responsibility_ref=_ref(36, "responsibility"),
        lease_ref=_ref(37, "lease"),
        policy_ref=_ref(38, "policy"),
        audit_ref=_ref(39, "audit"),
        evidence_refs=(_ref(40, "evidence"),),
    )
    assert request.source_message_envelope_ref.ref_type == "message_envelope"
    assert request.from_actor_ref.ref_type == "actor"
    assert request.to_actor_ref.ref_type == "actor"
    assert request.conversation_ref.ref_type == "conversation"
