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

from tiangong_kernel.l0_primitives.state import (
    CheckpointRef,
    ConstraintKind,
    ConstraintRef,
    CoreState,
    ExecutionStateRef,
    InvariantRef,
    RecoveryPointRef,
    RuntimeStateRef,
    StabilityRange,
    StateDeltaRef,
    StateKind,
    StateSnapshotRef,
    Violation,
    ViolationSeverity,
)


def test_state_objects_construct_and_serialize():
    snapshot = StateSnapshotRef(rid())
    delta = StateDeltaRef(rid(), before_ref=tref("before"), after_ref=tref("after"))
    checkpoint = CheckpointRef(rid(), snapshot_ref=snapshot)
    recovery_point = RecoveryPointRef(rid(), checkpoint_ref=checkpoint)
    invariant = InvariantRef(rid(), subject_ref=tref("state"))
    constraint = ConstraintRef(rid(), kind=ConstraintKind.INVARIANT, subject_ref=tref("state"))
    stability = StabilityRange("nominal", TimeRange(Timestamp(1), Timestamp(2)), 0.0, 1.0)
    violation = Violation(tref("violation"), ViolationSeverity.HIGH, constraint, (tref("evidence"),))
    objects = (
        RuntimeStateRef(rid()), ExecutionStateRef(rid()), snapshot, delta, checkpoint,
        recovery_point, invariant, constraint, stability, violation,
        CoreState(tref("core_state"), StateKind.SNAPSHOT, snapshot, delta, checkpoint, recovery_point, (invariant,), (constraint,), (violation,), stability),
    )
    for obj in objects:
        assert_value_object(obj)


def test_state_enum_values_are_stable():
    assert [item.value for item in StateKind] == ["runtime", "execution", "snapshot", "delta", "checkpoint", "recovery_point", "domain", "unknown"]
    assert [item.value for item in ConstraintKind] == ["precondition", "postcondition", "invariant", "resource_limit", "scope_boundary", "lease_boundary", "contract_boundary", "stability_range", "unknown"]
    assert [item.value for item in ViolationSeverity] == ["low", "medium", "high", "critical", "unknown"]
