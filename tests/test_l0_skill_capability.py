from dataclasses import FrozenInstanceError
import pytest
from tiangong_kernel.l0_primitives.identity import RefId
from tiangong_kernel.l0_primitives.serialization import stable_json_dumps, stable_hash

def rid(prefix: str = "ref") -> RefId:
    return RefId(f"{prefix}:" + "9" * 32)

def assert_frozen(obj):
    with pytest.raises(FrozenInstanceError):
        obj.schema_version = "x"

def assert_stable(obj):
    assert stable_json_dumps(obj) == stable_json_dumps(obj)
    assert stable_hash(obj) == stable_hash(obj)

from tiangong_kernel.l0_primitives.skill_capability import SkillRef, CapabilityRef, CapabilityKind, CapabilityState, CapabilityOriginRef, CapabilityRiskRef, CapabilityVersionRef

def test_skill_capability_objects_construct_freeze_serialize_hash_and_enum_values():
    skill = SkillRef(rid())
    origin = CapabilityOriginRef(rid())
    risk = CapabilityRiskRef(rid())
    version = CapabilityVersionRef(rid())
    capability = CapabilityRef(rid(), CapabilityKind.PROCEDURAL, CapabilityState.AVAILABLE, skill, origin, risk, version)
    assert CapabilityKind.COMMUNICATION.value == "communication"
    assert CapabilityState.AUTHORIZED.value == "authorized"
    for obj in (skill, origin, risk, version, capability):
        assert_frozen(obj); assert_stable(obj)
