from dataclasses import FrozenInstanceError

from tiangong_kernel.l0_primitives import stable_hash, stable_json_dumps, to_primitive
from tiangong_kernel.l0_primitives.content import ContentRef
from tiangong_kernel.l0_primitives.identity import CoreId, RefId
from tiangong_kernel.l0_primitives.message import CoreMessage, MessageRef, MessageRole, MessageState
from tiangong_kernel.l0_primitives.time import SequenceNo, Timestamp
from tiangong_kernel.l0_primitives.trace import CausalEventMetadata, SpanId, TraceId


def _trace():
    return CausalEventMetadata(
        trace_id=TraceId(CoreId("trace:" + "4" * 32)),
        span_id=SpanId(CoreId("span:" + "5" * 32)),
        sequence_no=SequenceNo(2),
    )


def test_message_construction_immutability_serialization_and_hash():
    message = CoreMessage(
        message_ref=MessageRef(RefId("message:" + "6" * 32)),
        role=MessageRole.USER,
        state=MessageState.RECORDED,
        created_at=Timestamp(123),
        trace=_trace(),
        content_ref=ContentRef(RefId("content:" + "7" * 32)),
        labels=("input",),
    )
    assert to_primitive(message)["role"] == "user"
    assert stable_json_dumps(message) == stable_json_dumps(message)
    assert stable_hash(message) == stable_hash(message)
    try:
        message.role = MessageRole.SYSTEM
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError("CoreMessage allowed mutation")


def test_message_enum_values_are_stable():
    assert [item.value for item in MessageRole] == ["system", "user", "assistant", "effect", "event", "internal", "unknown"]
    assert [item.value for item in MessageState] == ["created", "recorded", "superseded", "redacted", "rejected", "unknown"]
