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

from tiangong_kernel.l0_primitives.contract import ContractRef, ContractKind, ContractState, ContractScopeRef, ContractSatisfaction, ContractViolationRef, ContractVersionRef, ContractOriginRef

def test_contract_objects_construct_freeze_serialize_hash_and_enum_values():
    scope = ContractScopeRef(rid())
    version = ContractVersionRef(rid())
    origin = ContractOriginRef(rid())
    contract = ContractRef(rid(), ContractKind.SECURITY, ContractState.ACTIVE, ContractSatisfaction.SATISFIED, scope, version, origin)
    violation = ContractViolationRef(rid())
    assert ContractKind.RECOVERY.value == "recovery"
    assert ContractState.UNKNOWN.value == "unknown"
    assert ContractSatisfaction.NOT_APPLICABLE.value == "not_applicable"
    for obj in (scope, version, origin, contract, violation):
        assert_frozen(obj); assert_stable(obj)
