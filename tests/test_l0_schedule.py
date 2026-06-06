import tiangong_kernel.l0_primitives.schedule as module
from phase8_helpers import assert_enum_values, assert_module_dataclasses
from tiangong_kernel.l0_primitives.schedule import ScheduleKind, TriggerKind, TimerKind, ScheduleState, TriggerState, WakeupReason


def test_l0_schedule_objects_construct_freeze_serialize_hash_and_enum_values():
    assert_module_dataclasses(module)
    assert_enum_values(ScheduleKind, {'ONE_SHOT': 'one_shot', 'PLUGIN_TASK': 'plugin_task'})
    assert_enum_values(TriggerKind, {'TIME': 'time', 'LIFECYCLE_CHANGE': 'lifecycle_change'})
    assert_enum_values(TimerKind, {'DELAY': 'delay', 'SLEEP': 'sleep'})
    assert_enum_values(ScheduleState, {'WAITING': 'waiting', 'MISFIRED': 'misfired'})
    assert_enum_values(TriggerState, {'ACTIVE': 'active', 'EXPIRED': 'expired'})
    assert_enum_values(WakeupReason, {'TIME_ELAPSED': 'time_elapsed', 'FAILURE_HANDLED': 'failure_handled'})
