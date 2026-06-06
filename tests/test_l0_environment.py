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

from tiangong_kernel.l0_primitives.environment import EnvironmentKind, EnvironmentRef, EnvironmentState, SandboxKind, SandboxRef, IsolationLevel, IsolationBoundaryRef, EnvironmentFingerprint, EnvironmentCapabilityRef

def test_environment_objects_construct_freeze_serialize_hash_and_enum_values():
    env = EnvironmentRef(rid(), EnvironmentKind.CONTAINER, EnvironmentState.READY)
    sandbox = SandboxRef(rid(), SandboxKind.CONTAINER_SANDBOX, env)
    boundary = IsolationBoundaryRef(rid(), IsolationLevel.STRICT, env)
    fingerprint = EnvironmentFingerprint("abc")
    capability = EnvironmentCapabilityRef(rid(), env)
    assert EnvironmentKind.CODE_INTERPRETER.value == "code_interpreter"
    assert SandboxKind.HYBRID_SANDBOX.value == "hybrid_sandbox"
    assert IsolationLevel.VERIFIED.value == "verified"
    for obj in (env, sandbox, boundary, fingerprint, capability):
        assert_frozen(obj); assert_stable(obj)
