from tiangong_kernel.l0_primitives.content import ContentRef
from tiangong_kernel.l0_primitives.event import CoreEvent, EventRef, EventState, EventType
from tiangong_kernel.l0_primitives.identity import CoreId, RefId
from tiangong_kernel.l0_primitives.message import CoreMessage, MessageRef, MessageRole, MessageState
from tiangong_kernel.l0_primitives.metric import MetricKind, MetricPoint, MetricRef, MetricUnit, MetricValue
from tiangong_kernel.l0_primitives.serialization import stable_json_dumps, to_primitive
from tiangong_kernel.l0_primitives.signal import SignalKind, SignalRef, SignalStrength
from tiangong_kernel.l0_primitives.time import SequenceNo, Timestamp
from tiangong_kernel.l0_primitives.trace import CausalEventMetadata, SpanId, TraceId


def _trace():
    return CausalEventMetadata(
        trace_id=TraceId(CoreId("trace:" + "8" * 32)),
        span_id=SpanId(CoreId("span:" + "9" * 32)),
        sequence_no=SequenceNo(3),
    )


def test_phase2_objects_have_canonical_json_forms():
    event = CoreEvent(EventRef(RefId("event:" + "a" * 32)), EventType.MESSAGE_ADDED, EventState.RECORDED, Timestamp(1), _trace())
    message = CoreMessage(
        MessageRef(RefId("message:" + "b" * 32)),
        MessageRole.ASSISTANT,
        MessageState.RECORDED,
        Timestamp(2),
        _trace(),
        content_ref=ContentRef(RefId("content:" + "c" * 32)),
    )
    metric = MetricPoint(MetricRef(RefId("metric:" + "d" * 32)), MetricKind.COUNT, MetricValue(1), MetricUnit("items"), Timestamp(3))
    signal = (SignalRef(RefId("signal:" + "e" * 32)), SignalKind.HEALTH, SignalStrength(1.0))
    payload = (event, message, metric, signal)
    primitive = to_primitive(payload)
    assert primitive[0]["event_type"] == "message_added"
    assert primitive[1]["content_ref"]["value"]["value"] == "content:" + "c" * 32
    assert stable_json_dumps(payload) == stable_json_dumps(payload)
