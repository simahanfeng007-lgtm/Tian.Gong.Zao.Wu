from tiangong_kernel.l0_primitives.identity import CoreId, IdPrefix, RefId, TypedRef, validate_core_id
from tiangong_kernel.l0_primitives.result import ResultStatus, err, ok
from tiangong_kernel.l0_primitives.errors import CoreError, ErrorCode, ErrorSeverity
from tiangong_kernel.l0_primitives.serialization import stable_hash, stable_json_dumps, to_primitive
from tiangong_kernel.l0_primitives.time import ClockKind, Duration, SequenceNo, Timestamp
from tiangong_kernel.l0_primitives.trace import SpanId, TraceContext, TraceId


def test_phase1_core_objects_keep_stable_value_forms():
    core = CoreId("core:" + "1" * 32)
    ref = RefId("ref:" + "2" * 32)
    typed = TypedRef(ref, "sample")
    assert core.prefix == "core"
    assert typed.ref_type == "sample"
    assert to_primitive(Timestamp(1)) == {"epoch_ms": 1}
    assert stable_json_dumps((core, typed, Duration(5))) == stable_json_dumps((core, typed, Duration(5)))
    assert stable_hash((core, typed, SequenceNo(1))) == stable_hash((core, typed, SequenceNo(1)))


def test_phase1_result_first_contract():
    success = ok("done")
    failure = err(CoreError(ErrorCode.INVALID_VALUE, "bad", ErrorSeverity.RECOVERABLE))
    assert success.status is ResultStatus.OK
    assert success.is_ok and not success.is_error
    assert failure.status is ResultStatus.ERROR
    assert failure.is_error and not failure.is_ok
    assert not validate_core_id("bad-id").is_ok


def test_phase1_unknown_enum_fallbacks_exist():
    assert IdPrefix.UNKNOWN.value == "unknown"
    assert ErrorSeverity.UNKNOWN.value == "unknown"
    assert ResultStatus.UNKNOWN.value == "unknown"
    assert ClockKind.UNKNOWN.value == "unknown"


def test_phase1_trace_context_stays_fact_only():
    trace = TraceContext(
        trace_id=TraceId(CoreId("trace:" + "3" * 32)),
        span_id=SpanId(CoreId("span:" + "4" * 32)),
        sequence_no=SequenceNo(1),
    )
    primitive = to_primitive(trace)
    assert primitive["sequence_no"]["value"] == 1
    assert "causation_id" not in primitive
