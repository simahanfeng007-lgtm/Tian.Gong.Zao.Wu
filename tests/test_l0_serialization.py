from tiangong_kernel.l0_primitives import (
    CoreError,
    ErrorCode,
    IdPrefix,
    RefId,
    SequenceNo,
    TemporalWindow,
    TimeRange,
    Timestamp,
    TraceContext,
    TraceId,
    SpanId,
    stable_json_dumps,
    to_primitive,
    from_primitive,
)
from tiangong_kernel.l0_primitives.identity import CoreId


def test_l0_objects_convert_to_primitives_and_canonical_json():
    trace = TraceContext(
        trace_id=TraceId(CoreId("trace:" + "a" * 32)),
        span_id=SpanId(CoreId("span:" + "b" * 32)),
        sequence_no=SequenceNo(7),
    )
    primitive = to_primitive(trace)
    assert primitive["trace_id"]["value"]["value"] == "trace:" + "a" * 32
    assert primitive["sequence_no"]["value"] == 7
    assert stable_json_dumps(trace) == stable_json_dumps(trace)


def test_l0_nested_time_window_serializes_stably():
    window = TemporalWindow(TimeRange(Timestamp(10), Timestamp(20)), label="phase1")
    assert stable_json_dumps(window) == '{"label":"phase1","range":{"end":{"epoch_ms":20},"start":{"epoch_ms":10}}}'


def test_from_primitive_supports_phase1_simple_types():
    restored = from_primitive(CoreId, {"value": "core:" + "c" * 32})
    assert restored == CoreId("core:" + "c" * 32)
    assert from_primitive(IdPrefix, "trace") is IdPrefix.TRACE


def test_error_serialization_uses_enum_values():
    error = CoreError(code=ErrorCode.INVALID_VALUE, message="bad")
    assert to_primitive(error)["code"] == "invalid_value"
