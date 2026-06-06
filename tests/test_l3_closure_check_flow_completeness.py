from tiangong_kernel.l0_primitives.identity import RefId, TypedRef
from tiangong_kernel.l3_orchestration import L3ClosureCheckKind, L3ClosureCheckRequest, L3ClosureCheckResult


def typed(index: int, ref_type: str) -> TypedRef:
    return TypedRef(RefId(f"ref:{index:032x}"), ref_type)


def test_l3_closure_check_can_include_flow_completeness():
    request = L3ClosureCheckRequest(
        request_ref=typed(50, "l3_closure_request"),
        requested_check_kinds=(L3ClosureCheckKind.FLOW_COMPLETENESS,),
    )
    result = L3ClosureCheckResult(
        result_ref=typed(51, "l3_closure_result"),
        request_ref=request.request_ref,
        passed_check_kinds=(L3ClosureCheckKind.FLOW_COMPLETENESS,),
        readiness_score=1.0,
    )
    assert request.request_only is True
    assert result.report_only is True
    assert L3ClosureCheckKind.FLOW_COMPLETENESS in result.passed_check_kinds
