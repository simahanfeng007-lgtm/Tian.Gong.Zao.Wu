from dataclasses import FrozenInstanceError

from tiangong_kernel.l0_primitives.context import (
    BeliefStateRef,
    ContextBoundary,
    ContextDigest,
    ContextKind,
    ContextOriginRef,
    ContextRef,
    ContextWindow,
    WorldStateRef,
)
from tiangong_kernel.l0_primitives.identity import RefId, TypedRef
from tiangong_kernel.l0_primitives.serialization import stable_hash, stable_json_dumps


def rid(prefix: str = "ref") -> RefId:
    return RefId(f"{prefix}:" + "3" * 32)


def tref(kind: str = "context") -> TypedRef:
    return TypedRef(rid("ref"), kind)


def test_context_objects_construct_immutable_and_stable():
    window = ContextWindow(rid(), trace_ref=tref("trace"), span_ref=tref("span"))
    boundary = ContextBoundary(visible_boundary_ref=tref("visible"), reference_boundary_ref=tref("reference"), usable_boundary_ref=tref("usable"))
    digest = ContextDigest("a" * 64, source_ref=tref("source"))
    origin = ContextOriginRef(rid(), origin_ref=tref("event"))
    belief = BeliefStateRef(rid(), evidence_refs=(tref("evidence"),))
    world = WorldStateRef(rid(), scope_ref=tref("scope"))
    context = ContextRef(
        rid(),
        kind=ContextKind.CONVERSATION,
        window=window,
        boundary=boundary,
        digest=digest,
        origin_ref=origin,
        actor_ref=tref("actor"),
        scope_ref=tref("scope"),
        belief_state_ref=belief,
        world_state_ref=world,
    )
    assert "conversation" in stable_json_dumps(context)
    assert stable_hash(context) == stable_hash(context)
    try:
        context.kind = ContextKind.SYSTEM_CONTEXT
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError("ContextRef allowed mutation")


def test_context_enum_values_are_stable():
    assert ContextKind.CONVERSATION.value == "conversation"
    assert ContextKind.RUN_CONTEXT.value == "run_context"
    assert ContextKind.TASK_CONTEXT.value == "task_context"
    assert ContextKind.TOOL_CONTEXT.value == "tool_context"
    assert ContextKind.MEMORY_CONTEXT.value == "memory_context"
    assert ContextKind.OBSERVATION_CONTEXT.value == "observation_context"
    assert ContextKind.SYSTEM_CONTEXT.value == "system_context"
    assert ContextKind.RECOVERY_CONTEXT.value == "recovery_context"
    assert ContextKind.UNKNOWN.value == "unknown"
