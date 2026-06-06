from dataclasses import FrozenInstanceError

from tiangong_kernel.l0_primitives.forgetting import (
    DecayRate,
    DecayTrace,
    ForgettingKind,
    ForgettingRef,
    ForgettingState,
    InterferenceTrace,
    PruningRef,
    RetentionScore,
    RetentionTrace,
    RevisionRef,
    SuppressionRef,
)
from tiangong_kernel.l0_primitives.identity import RefId, TypedRef
from tiangong_kernel.l0_primitives.serialization import stable_hash, stable_json_dumps


def rid(prefix: str = "ref") -> RefId:
    return RefId(f"{prefix}:" + "2" * 32)


def tref(kind: str = "memory") -> TypedRef:
    return TypedRef(rid("ref"), kind)


def test_forgetting_objects_construct_immutable_and_stable():
    retention = RetentionTrace(tref("trace"), memory_ref=tref(), score=RetentionScore(0.8))
    decay = DecayTrace(tref("trace"), memory_ref=tref(), decay_rate=DecayRate(0.1))
    interference = InterferenceTrace(tref("trace"), source_memory_ref=tref(), target_memory_ref=tref(), strength=0.5)
    suppression = SuppressionRef(rid(), memory_ref=tref())
    pruning = PruningRef(rid(), memory_ref=tref())
    revision = RevisionRef(rid(), previous_ref=tref("old"), revised_ref=tref("new"))
    item = ForgettingRef(
        rid(),
        kind=ForgettingKind.PASSIVE_DECAY,
        state=ForgettingState.DECAYING,
        retention_trace=retention,
        decay_trace=decay,
        interference_trace=interference,
        suppression_ref=suppression,
        pruning_ref=pruning,
        revision_ref=revision,
    )
    assert "passive_decay" in stable_json_dumps(item)
    assert stable_hash(item) == stable_hash(item)
    try:
        item.state = ForgettingState.ARCHIVED
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError("ForgettingRef allowed mutation")


def test_forgetting_enum_values_are_stable():
    assert ForgettingKind.PASSIVE_DECAY.value == "passive_decay"
    assert ForgettingKind.ACTIVE_DELETION.value == "active_deletion"
    assert ForgettingKind.SAFETY_TRIGGERED.value == "safety_triggered"
    assert ForgettingKind.ADAPTIVE_REINFORCED.value == "adaptive_reinforced"
    assert ForgettingKind.INTERFERENCE_BASED.value == "interference_based"
    assert ForgettingKind.REVISION_BASED.value == "revision_based"
    assert ForgettingKind.SUPPRESSION.value == "suppression"
    assert ForgettingKind.PRUNING.value == "pruning"
    assert ForgettingKind.UNKNOWN.value == "unknown"
    assert ForgettingState.PROPOSED.value == "proposed"
    assert ForgettingState.SCHEDULED.value == "scheduled"
    assert ForgettingState.DECAYING.value == "decaying"
    assert ForgettingState.SUPPRESSED.value == "suppressed"
    assert ForgettingState.PRUNED.value == "pruned"
    assert ForgettingState.REVISED.value == "revised"
    assert ForgettingState.DELETED.value == "deleted"
    assert ForgettingState.BLOCKED.value == "blocked"
    assert ForgettingState.ARCHIVED.value == "archived"
    assert ForgettingState.UNKNOWN.value == "unknown"
