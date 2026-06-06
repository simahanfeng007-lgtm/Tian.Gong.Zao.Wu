from tiangong_kernel.l0_primitives.content import ContentRef
from tiangong_kernel.l0_primitives.event import CoreEvent, EventRef, EventState, EventType
from tiangong_kernel.l0_primitives.identity import CoreId, RefId
from tiangong_kernel.l0_primitives.message import CoreMessage, MessageRef, MessageRole, MessageState
from tiangong_kernel.l0_primitives.serialization import stable_hash
from tiangong_kernel.l0_primitives.time import SequenceNo, Timestamp
from tiangong_kernel.l0_primitives.trace import CausalEventMetadata, SpanId, TraceId


def _trace(sequence: int):
    return CausalEventMetadata(
        trace_id=TraceId(CoreId("trace:" + "f" * 32)),
        span_id=SpanId(CoreId("span:" + "1" * 32)),
        sequence_no=SequenceNo(sequence),
    )


def test_phase2_stable_hash_is_repeatable_and_sensitive_to_fact_changes():
    event_a = CoreEvent(EventRef(RefId("event:" + "2" * 32)), EventType.RUN_CREATED, EventState.RECORDED, Timestamp(1), _trace(1))
    event_b = CoreEvent(EventRef(RefId("event:" + "2" * 32)), EventType.RUN_CREATED, EventState.RECORDED, Timestamp(2), _trace(1))
    assert stable_hash(event_a) == stable_hash(event_a)
    assert stable_hash(event_a) != stable_hash(event_b)


def test_phase2_hash_handles_nested_message_content_ref():
    message = CoreMessage(
        MessageRef(RefId("message:" + "3" * 32)),
        MessageRole.EVENT,
        MessageState.RECORDED,
        Timestamp(5),
        _trace(2),
        content_ref=ContentRef(RefId("content:" + "4" * 32)),
    )
    assert len(stable_hash(message)) == 64
