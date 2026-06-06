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

from tiangong_kernel.l0_primitives.resource import ResourceKind, ResourceRef, ResourceQuantity, ResourceUsage, ResourceBudget, ResourceLimit, ResourcePressure, EnergyBudget

def test_resource_objects_construct_freeze_serialize_hash_and_enum_values():
    quantity = ResourceQuantity(10.0, "unit", ResourceKind.COMPUTE)
    resource = ResourceRef(rid(), ResourceKind.CONTEXT)
    usage = ResourceUsage(rid(), resource, quantity)
    budget = ResourceBudget(rid(), resource, quantity)
    limit = ResourceLimit(rid(), resource, quantity)
    pressure = ResourcePressure(rid(), resource, usage, 0.5)
    energy = EnergyBudget(rid(), quantity)
    assert ResourceKind.ATTENTION.value == "attention"
    assert ResourceKind.UNKNOWN.value == "unknown"
    for obj in (quantity, resource, usage, budget, limit, pressure, energy):
        assert_frozen(obj); assert_stable(obj)
