from tiangong_kernel.l0_primitives.errors import CoreError, ErrorCode, ErrorSeverity
from tiangong_kernel.l0_primitives.identity import validate_core_id
from tiangong_kernel.l0_primitives.result import ResultStatus, err, ok


def test_result_helpers_return_core_result_objects():
    success = ok("value")
    failure = err(CoreError(ErrorCode.UNKNOWN, "unknown", ErrorSeverity.UNKNOWN))
    assert success.status is ResultStatus.OK
    assert success.value == "value"
    assert failure.status is ResultStatus.ERROR
    assert failure.error is not None


def test_validation_uses_result_first_for_invalid_core_id():
    result = validate_core_id("not-a-core-id")
    assert result.status is ResultStatus.ERROR
    assert result.error is not None
    assert result.error.code is ErrorCode.INVALID_ID
