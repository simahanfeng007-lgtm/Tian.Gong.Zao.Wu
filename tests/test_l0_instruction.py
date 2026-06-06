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

from tiangong_kernel.l0_primitives.instruction import InstructionRef, InstructionKind, InstructionAuthority, InstructionSource, InstructionPriority, InstructionState, InstructionConflictRef, DirectiveRef

def test_instruction_objects_construct_freeze_serialize_hash_and_enum_values():
    source = InstructionSource(authority=InstructionAuthority.USER)
    priority = InstructionPriority(10)
    conflict = InstructionConflictRef(rid())
    directive = DirectiveRef(rid(), InstructionAuthority.SYSTEM, source)
    instruction = InstructionRef(rid(), InstructionKind.USER_REQUEST, InstructionAuthority.USER, source, priority, InstructionState.ACTIVE, conflict, directive)
    assert InstructionKind.RECOVERY_DIRECTIVE.value == "recovery_directive"
    assert InstructionAuthority.ROOT.value == "root"
    assert InstructionState.UNKNOWN.value == "unknown"
    for obj in (source, priority, conflict, directive, instruction):
        assert_frozen(obj); assert_stable(obj)
