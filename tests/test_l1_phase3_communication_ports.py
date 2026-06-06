import inspect
from dataclasses import is_dataclass
from typing import get_origin, get_type_hints

from tiangong_kernel.l0_primitives.communication import ChannelRef, ConversationRef, HandoffRef, ProtocolRef
from tiangong_kernel.l0_primitives.message import MessageRef
from tiangong_kernel.l0_primitives.result import CoreResult
from tiangong_kernel.l1_ports.port_result import PortResult
import tiangong_kernel.l1_ports.communication_ports as ports


PORT_CLASSES = [
    ports.MessagePort,
    ports.ChannelPort,
    ports.ProtocolPort,
    ports.HandoffPort,
    ports.ConversationPort,
]
DATA_CLASSES = [
    ports.CommunicationPortBoundary,
    ports.MessageSubmitRequest,
    ports.MessageSubmitResponse,
    ports.MessageReadRequest,
    ports.MessageReadResponse,
    ports.ChannelOpenIntentRequest,
    ports.ChannelOpenIntentResponse,
    ports.ProtocolDeclareRequest,
    ports.ProtocolDeclareResponse,
    ports.HandoffSubmitRequest,
    ports.HandoffSubmitResponse,
    ports.ConversationReferenceRequest,
    ports.ConversationReferenceResponse,
]


def _return_is_result(method):
    hint = get_type_hints(method)["return"]
    return get_origin(hint) in {CoreResult, PortResult}


def test_phase3_communication_ports_are_abstract():
    for port_cls in PORT_CLASSES:
        assert inspect.isabstract(port_cls)
        assert port_cls.__name__.endswith("Port")


def test_phase3_communication_methods_return_result_wrappers():
    for port_cls in PORT_CLASSES:
        for method_name in port_cls.__abstractmethods__:
            assert _return_is_result(getattr(port_cls, method_name))


def test_phase3_communication_data_objects_are_frozen_slots_dataclasses():
    for cls in DATA_CLASSES:
        assert is_dataclass(cls)
        assert cls.__dataclass_params__.frozen is True
        assert hasattr(cls, "__slots__")


def test_phase3_communication_requests_use_l0_communication_objects():
    assert get_type_hints(ports.MessageSubmitRequest)["message_ref"] is MessageRef
    assert get_type_hints(ports.ChannelOpenIntentRequest)["channel_ref"] is ChannelRef
    assert get_type_hints(ports.ProtocolDeclareRequest)["protocol_ref"] is ProtocolRef
    assert get_type_hints(ports.HandoffSubmitRequest)["handoff_ref"] is HandoffRef
    assert get_type_hints(ports.ConversationReferenceRequest)["conversation_ref"] is ConversationRef
