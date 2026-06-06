from dataclasses import FrozenInstanceError, fields

from tiangong_kernel.l0_primitives.identity import RefId, TypedRef
from tiangong_kernel.l0_primitives.serialization import stable_hash, stable_json_dumps
from tiangong_kernel.l0_primitives.time import TimeRange, Timestamp


def rid(prefix: str = "ref") -> RefId:
    return RefId(f"{prefix}:" + "1" * 32)


def tref(kind: str = "sample") -> TypedRef:
    return TypedRef(rid("ref"), kind)


def assert_value_object(obj):
    dumped = stable_json_dumps(obj)
    digest = stable_hash(obj)
    assert isinstance(dumped, str)
    assert isinstance(digest, str)
    assert len(digest) == 64
    field_name = fields(obj)[0].name
    try:
        setattr(obj, field_name, getattr(obj, field_name))
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError(f"{type(obj).__name__} allowed mutation")

from tiangong_kernel.l0_primitives.deletion import DeletionKind, DeletionRef
from tiangong_kernel.l0_primitives.failure import FailureKind, FailureRef
from tiangong_kernel.l0_primitives.lifecycle import LifecycleRef, LifecycleState
from tiangong_kernel.l0_primitives.state import RuntimeStateRef, StateKind
from tiangong_kernel.l0_primitives.transaction import TransactionKind, TransactionRef


def test_phase4_objects_have_stable_json():
    objects = (
        RuntimeStateRef(rid(), StateKind.RUNTIME),
        LifecycleRef(rid(), LifecycleState.CREATED),
        FailureRef(rid(), FailureKind.GOAL_FAILURE),
        TransactionRef(rid(), TransactionKind.SINGLE_EFFECT),
        DeletionRef(rid(), DeletionKind.USER_REQUESTED),
    )
    for obj in objects:
        first = stable_json_dumps(obj)
        second = stable_json_dumps(obj)
        assert first == second
        assert "schema_version" in first
