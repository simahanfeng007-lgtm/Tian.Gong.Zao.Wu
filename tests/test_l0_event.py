from dataclasses import FrozenInstanceError

from tiangong_kernel.l0_primitives import stable_hash, stable_json_dumps, to_primitive
from tiangong_kernel.l0_primitives.event import CoreEvent, EventMeta, EventPayloadRef, EventRef, EventState, EventType
from tiangong_kernel.l0_primitives.identity import CoreId, RefId
from tiangong_kernel.l0_primitives.time import SequenceNo, Timestamp
from tiangong_kernel.l0_primitives.trace import CausalEventMetadata, SpanId, TraceId


def _trace():
    return CausalEventMetadata(
        trace_id=TraceId(CoreId("trace:" + "1" * 32)),
        span_id=SpanId(CoreId("span:" + "2" * 32)),
        sequence_no=SequenceNo(1),
    )


def test_event_construction_immutability_serialization_and_hash():
    event = CoreEvent(
        event_ref=EventRef(RefId("event:" + "a" * 32)),
        event_type=EventType.RUN_CREATED,
        state=EventState.RECORDED,
        created_at=Timestamp(1000),
        trace=_trace(),
        payload_ref=EventPayloadRef(RefId("payload:" + "b" * 32), payload_type="content"),
        meta=EventMeta(tags=("phase2",), attributes=(("layer", "l0"),)),
    )
    assert to_primitive(event)["event_type"] == "run_created"
    assert stable_json_dumps(event) == stable_json_dumps(event)
    assert stable_hash(event) == stable_hash(event)
    try:
        event.state = EventState.CLOSED
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError("CoreEvent allowed mutation")


def test_event_enum_values_are_stable():
    assert [item.value for item in EventType] == [
        "run_created",
        "state_changed",
        "message_added",
        "action_proposed",
        "decision_recorded",
        "effect_requested",
        "effect_accepted",
        "effect_rejected",
        "checkpoint_created",
        "error_raised",
        "lifecycle_changed",
        "signal_recorded",
        "metric_recorded",
        "run_closed",
        "unknown",
    ]
    assert EventState.UNKNOWN.value == "unknown"
