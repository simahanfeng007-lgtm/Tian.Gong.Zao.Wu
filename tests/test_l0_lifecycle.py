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

from tiangong_kernel.l0_primitives.lifecycle import (
    LifecyclePhase,
    LifecyclePolicyRef,
    LifecycleReason,
    LifecycleRef,
    LifecycleState,
    LifecycleTransitionRef,
)


def test_lifecycle_objects_construct_and_serialize():
    objects = (
        LifecycleRef(rid(), LifecycleState.ACTIVE, LifecyclePhase.OPERATION),
        LifecycleTransitionRef(rid(), LifecycleState.CREATED, LifecycleState.ACTIVE, tref("subject")),
        LifecycleReason("user_requested", tref("evidence")),
        LifecyclePolicyRef(rid(), "retention"),
    )
    for obj in objects:
        assert_value_object(obj)


def test_lifecycle_enum_values_are_stable():
    assert [item.value for item in LifecycleState] == [
        "proposed", "created", "initializing", "active", "paused", "degraded", "blocked", "recovering",
        "suspended", "completed", "failed", "terminating", "terminated", "archived", "deprecated", "revoked",
        "quarantined", "deleted", "unknown",
    ]
    assert [item.value for item in LifecyclePhase] == ["birth", "activation", "operation", "adaptation", "recovery", "decline", "termination", "archival", "unknown"]
