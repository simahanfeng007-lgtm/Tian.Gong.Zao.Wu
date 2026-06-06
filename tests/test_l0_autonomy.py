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

from tiangong_kernel.l0_primitives.autonomy import AutonomyLevel, AgencyLevel, ControlModeRef, OversightMode, ControlModeState, AutonomyBoundaryRef, AgencyBoundaryRef

def test_autonomy_objects_construct_freeze_serialize_hash_and_enum_values():
    autonomy_boundary = AutonomyBoundaryRef(rid())
    agency_boundary = AgencyBoundaryRef(rid())
    control = ControlModeRef(rid(), AutonomyLevel.L3_ACT_WITH_APPROVAL, AgencyLevel.G3_REQUEST_EFFECT, OversightMode.HUMAN_IN_THE_LOOP, ControlModeState.ACTIVE, autonomy_boundary, agency_boundary)
    assert AutonomyLevel.L0_MANUAL.value == "l0_manual"
    assert AgencyLevel.G5_COMMIT_IRREVERSIBLE.value == "g5_commit_irreversible"
    assert OversightMode.UNKNOWN.value == "unknown"
    for obj in (autonomy_boundary, agency_boundary, control):
        assert_frozen(obj); assert_stable(obj)
