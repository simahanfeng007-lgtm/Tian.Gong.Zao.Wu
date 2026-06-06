from l3_phase5_builders import build_l3_phase5_objects
from tiangong_kernel.l3_orchestration import (
    ExecutionDispatchRequest,
    ExecutionRequest,
    ExecutionResultRoutingAdvice,
    ExecutionTokenRef,
)


def test_execution_request_is_future_l4_request_only():
    objects = build_l3_phase5_objects()
    request = objects["execution_request"]
    dispatch = objects["dispatch_request"]
    assert isinstance(request, ExecutionRequest)
    assert isinstance(dispatch, ExecutionDispatchRequest)
    assert request.request_only is True
    assert dispatch.request_only is True
    assert not hasattr(request, "executor")
    assert not hasattr(dispatch, "dispatch_runtime")
    assert not hasattr(dispatch, "tool_executor")


def test_execution_token_ref_is_reference_only():
    objects = build_l3_phase5_objects()
    token = objects["token_ref"]
    assert isinstance(token, ExecutionTokenRef)
    assert token.reference_only is True
    assert not hasattr(token, "token_value")
    assert not hasattr(token, "grant")


def test_execution_result_failure_retry_and_fallback_are_routing_advice_only():
    objects = build_l3_phase5_objects()
    result_routing = objects["result_routing"]
    retry = objects["retry_advice"]
    fallback = objects["fallback_advice"]
    assert isinstance(result_routing, ExecutionResultRoutingAdvice)
    assert result_routing.advisory_only is True
    assert retry.advisory_only is True
    assert fallback.advisory_only is True
    assert not hasattr(retry, "retry_now")
    assert not hasattr(fallback, "execute_fallback")
