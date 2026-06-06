from dataclasses import FrozenInstanceError

from tiangong_kernel.l0_primitives.identity import RefId, TypedRef
from tiangong_kernel.l0_primitives.memory import (
    MemoryConfidence,
    MemoryKind,
    MemoryOriginRef,
    MemoryRef,
    MemoryRetentionRef,
    MemoryState,
    MemoryTraceRef,
)
from tiangong_kernel.l0_primitives.serialization import stable_hash, stable_json_dumps


def rid(prefix: str = "ref") -> RefId:
    return RefId(f"{prefix}:" + "1" * 32)


def tref(kind: str = "memory") -> TypedRef:
    return TypedRef(rid("ref"), kind)


def test_memory_objects_construct_immutable_and_stable():
    trace = MemoryTraceRef(rid(), memory_ref=tref())
    origin = MemoryOriginRef(rid(), origin_ref=tref("event"), trace_ref=trace)
    confidence = MemoryConfidence(0.75, evidence_refs=(tref("evidence"),))
    retention = MemoryRetentionRef(rid(), memory_ref=tref(), policy_ref=tref("policy"))
    memory = MemoryRef(
        rid(),
        kind=MemoryKind.SEMANTIC,
        state=MemoryState.ACTIVE,
        trace_ref=trace,
        origin_ref=origin,
        confidence=confidence,
        retention_ref=retention,
    )
    assert "semantic" in stable_json_dumps(memory)
    assert stable_hash(memory) == stable_hash(memory)
    try:
        memory.state = MemoryState.ARCHIVED
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError("MemoryRef allowed mutation")


def test_memory_enum_values_are_stable():
    assert MemoryKind.WORKING.value == "working"
    assert MemoryKind.EPISODIC.value == "episodic"
    assert MemoryKind.SEMANTIC.value == "semantic"
    assert MemoryKind.PROCEDURAL.value == "procedural"
    assert MemoryKind.RESOURCE.value == "resource"
    assert MemoryKind.SELF.value == "self"
    assert MemoryKind.USER.value == "user"
    assert MemoryKind.SYSTEM.value == "system"
    assert MemoryKind.UNKNOWN.value == "unknown"
    assert MemoryState.CANDIDATE.value == "candidate"
    assert MemoryState.ACTIVE.value == "active"
    assert MemoryState.REINFORCED.value == "reinforced"
    assert MemoryState.CONSOLIDATING.value == "consolidating"
    assert MemoryState.STABLE.value == "stable"
    assert MemoryState.DECAYING.value == "decaying"
    assert MemoryState.SUPPRESSED.value == "suppressed"
    assert MemoryState.DEPRECATED.value == "deprecated"
    assert MemoryState.ARCHIVED.value == "archived"
    assert MemoryState.FORGOTTEN.value == "forgotten"
    assert MemoryState.UNKNOWN.value == "unknown"
