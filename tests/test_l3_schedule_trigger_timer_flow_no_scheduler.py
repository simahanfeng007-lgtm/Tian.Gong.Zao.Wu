from tiangong_kernel.l0_primitives.identity import RefId, TypedRef
from tiangong_kernel.l3_orchestration import ScheduleTriggerTimerFlow


def typed(index: int, ref_type: str) -> TypedRef:
    return TypedRef(RefId(f"ref:{index:032x}"), ref_type)


def test_l3_schedule_trigger_timer_flow_is_trigger_refs_only():
    flow = ScheduleTriggerTimerFlow(
        schedule_refs=(typed(20, "schedule_ref"),),
        trigger_refs=(typed(21, "trigger_ref"),),
        timer_refs=(typed(22, "timer_ref"),),
    )
    assert flow.schedule_refs and flow.trigger_refs and flow.timer_refs
    assert flow.background_task_started is False
    assert flow.no_execution is True
    assert flow.no_persistence is True
