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

from tiangong_kernel.l0_primitives.transaction import (
    CommitRef,
    CompensationRef,
    CompensationState,
    IdempotencyKey,
    ReversibilityKind,
    RollbackRef,
    TransactionKind,
    TransactionRef,
    TransactionState,
)


def test_transaction_objects_construct_and_serialize():
    transaction = TransactionRef(rid(), TransactionKind.SAGA, TransactionState.AUTHORIZED)
    compensation = CompensationRef(rid(), CompensationState.AVAILABLE, tref("effect"))
    key = IdempotencyKey("idem-1", tref("scope"))
    commit = CommitRef(rid(), transaction, (tref("effect"),))
    rollback = RollbackRef(rid(), transaction, compensation)
    for obj in (transaction, compensation, key, commit, rollback):
        assert_value_object(obj)


def test_transaction_enum_values_are_stable():
    assert [item.value for item in ReversibilityKind] == ["idempotent", "reversible", "compensable", "irreversible", "unknown"]
    assert [item.value for item in TransactionKind] == ["single_effect", "effect_chain", "saga", "checkpointed", "human_approved", "recovery", "unknown"]
    assert [item.value for item in TransactionState] == ["proposed", "authorized", "in_progress", "partially_committed", "committed", "compensating", "compensated", "rolling_back", "rolled_back", "failed", "cancelled", "unknown"]
    assert [item.value for item in CompensationState] == ["not_required", "available", "scheduled", "running", "succeeded", "failed", "manual_required", "unknown"]
