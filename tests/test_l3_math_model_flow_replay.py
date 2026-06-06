from __future__ import annotations

from tiangong_kernel.l0_primitives.identity import RefId, TypedRef
from tiangong_kernel.l3_orchestration.math_model_engine_flow import ModelReplayFlow


def _ref(suffix: int) -> TypedRef:
    return TypedRef(RefId(f"ref:{suffix:032x}"), "math_replay")


def test_l3_math_model_replay_flow_is_reference_only() -> None:
    flow = ModelReplayFlow(replay_request_ref=_ref(1), replay_result_ref=_ref(2), difference_refs=(_ref(3),))

    assert flow.replay_request_ref is not None
    assert flow.replay_result_ref is not None
    assert len(flow.difference_refs) == 1
    assert flow.request_only is True
    assert flow.no_tool_action is True
