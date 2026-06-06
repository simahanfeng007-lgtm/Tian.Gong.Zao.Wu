from dataclasses import FrozenInstanceError
import pytest
from tiangong_kernel.l0_primitives.identity import RefId
from tiangong_kernel.l0_primitives.serialization import stable_json_dumps, stable_hash

def rid(prefix: str = "ref") -> RefId:
    return RefId(f"{prefix}:" + "7" * 32)

def assert_frozen(obj):
    with pytest.raises(FrozenInstanceError):
        obj.schema_version = "x"

def assert_stable(obj):
    assert stable_json_dumps(obj) == stable_json_dumps(obj)
    assert stable_hash(obj) == stable_hash(obj)

from tiangong_kernel.l0_primitives.value import ValueRef, ValueKind, PreferenceRef, PreferenceKind, PreferenceState, ObjectiveRef, ObjectiveKind, ObjectivePriority, UtilitySignalRef, TradeoffRef

def test_value_objects_construct_freeze_serialize_hash_and_enum_values():
    value = ValueRef(rid(), ValueKind.SAFETY)
    preference = PreferenceRef(rid(), PreferenceKind.USER_PREFERENCE, PreferenceState.ACTIVE, value)
    objective = ObjectiveRef(rid(), ObjectiveKind.TASK_SUCCESS, ObjectivePriority(5))
    utility = UtilitySignalRef(rid(), objective_ref=objective, value_ref=value)
    tradeoff = TradeoffRef(rid(), (value,), (preference,), (objective,))
    assert ValueKind.EXECUTION_POWER.value == "execution_power"
    assert PreferenceKind.UNKNOWN.value == "unknown"
    assert ObjectiveKind.USER_SATISFACTION.value == "user_satisfaction"
    for obj in (value, preference, objective, utility, tradeoff):
        assert_frozen(obj); assert_stable(obj)
