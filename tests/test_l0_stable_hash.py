from tiangong_kernel.l0_primitives import CoreId, TraceContext, TraceId, SpanId, SequenceNo, stable_hash


def test_stable_hash_is_repeatable_for_same_object():
    trace = TraceContext(
        trace_id=TraceId(CoreId("trace:" + "1" * 32)),
        span_id=SpanId(CoreId("span:" + "2" * 32)),
        sequence_no=SequenceNo(3),
    )
    assert stable_hash(trace) == stable_hash(trace)


def test_stable_hash_is_independent_of_dict_insertion_order():
    left = {"b": 2, "a": 1}
    right = {"a": 1, "b": 2}
    assert stable_hash(left) == stable_hash(right)


def test_stable_hash_changes_when_fact_changes():
    a = TraceContext(TraceId(CoreId("trace:" + "3" * 32)), SpanId(CoreId("span:" + "4" * 32)), sequence_no=SequenceNo(1))
    b = TraceContext(TraceId(CoreId("trace:" + "3" * 32)), SpanId(CoreId("span:" + "4" * 32)), sequence_no=SequenceNo(2))
    assert stable_hash(a) != stable_hash(b)
