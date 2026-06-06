from dataclasses import FrozenInstanceError
import pytest
from tiangong_kernel.l0_primitives.identity import RefId
from tiangong_kernel.l0_primitives.serialization import stable_json_dumps, stable_hash

def rid(prefix: str = "ref") -> RefId:
    return RefId(f"{prefix}:" + "9" * 32)

def assert_frozen(obj):
    with pytest.raises(FrozenInstanceError):
        obj.schema_version = "x"

def assert_stable(obj):
    assert stable_json_dumps(obj) == stable_json_dumps(obj)
    assert stable_hash(obj) == stable_hash(obj)

from tiangong_kernel.l0_primitives.communication import CommunicationRef, MessageEnvelopeRef, MessageKind, MessageDirection, ChannelRef, ChannelKind, ProtocolRef, ProtocolKind, DeliveryState, ReplyToRef, ConversationRef, HandoffRef

def test_communication_objects_construct_freeze_serialize_hash_and_enum_values():
    channel = ChannelRef(rid(), ChannelKind.INTERNAL)
    protocol = ProtocolRef(rid(), ProtocolKind.INTERNAL)
    communication = CommunicationRef(rid(), channel, protocol)
    envelope = MessageEnvelopeRef(rid(), MessageKind.REQUEST, MessageDirection.OUTBOUND, DeliveryState.CREATED, channel_ref=channel, protocol_ref=protocol)
    reply = ReplyToRef(rid(), envelope)
    conversation = ConversationRef(rid(), envelope)
    handoff = HandoffRef(rid())
    assert MessageKind.HEARTBEAT.value == "heartbeat"
    assert ChannelKind.AUDIT.value == "audit"
    assert ProtocolKind.JSON_RPC.value == "json_rpc"
    assert DeliveryState.ACKED.value == "acked"
    for obj in (channel, protocol, communication, envelope, reply, conversation, handoff):
        assert_frozen(obj); assert_stable(obj)
