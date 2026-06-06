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

from tiangong_kernel.l0_primitives.policy import PolicyRef, PolicyKind, PolicyState, NormRef, NormKind, GovernanceRef, GovernanceDomain, PolicyConflictRef, EnforcementModeRef

def test_policy_objects_construct_freeze_serialize_hash_and_enum_values():
    norm = NormRef(rid(), NormKind.PROHIBITION)
    governance = GovernanceRef(rid(), GovernanceDomain.PRIVACY)
    conflict = PolicyConflictRef(rid())
    mode = EnforcementModeRef(rid())
    policy = PolicyRef(rid(), PolicyKind.HUMAN_APPROVAL, PolicyState.ACTIVE, (norm,), governance, conflict, mode)
    assert PolicyKind.DATA_GOVERNANCE.value == "data_governance"
    assert NormKind.EXCEPTION.value == "exception"
    assert GovernanceDomain.UNKNOWN.value == "unknown"
    for obj in (norm, governance, conflict, mode, policy):
        assert_frozen(obj); assert_stable(obj)
