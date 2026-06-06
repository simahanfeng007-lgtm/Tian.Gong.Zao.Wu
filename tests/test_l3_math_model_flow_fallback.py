from __future__ import annotations

from tiangong_kernel.l0_primitives.identity import RefId, TypedRef
from tiangong_kernel.l3_orchestration.math_model_engine_flow import ModelFallbackFlow


def _ref(suffix: int) -> TypedRef:
    return TypedRef(RefId(f"ref:{suffix:032x}"), "math_fallback")


def test_l3_math_model_fallback_flow_is_safe_default_only() -> None:
    flow = ModelFallbackFlow(fallback_reason_ref=_ref(1), safe_default_result_ref=_ref(2))

    assert flow.fallback_reason_ref is not None
    assert flow.safe_default_result_ref is not None
    assert flow.advisory_only is True
    assert flow.no_final_decision is True
    assert flow.no_tool_action is True
