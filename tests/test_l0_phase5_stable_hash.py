from tiangong_kernel.l0_primitives.context import ContextKind, ContextRef
from tiangong_kernel.l0_primitives.forgetting import ForgettingKind, ForgettingRef, ForgettingState
from tiangong_kernel.l0_primitives.health import HealthRef, HealthState
from tiangong_kernel.l0_primitives.identity import RefId
from tiangong_kernel.l0_primitives.learning import LearningKind, LearningRef, LearningState
from tiangong_kernel.l0_primitives.memory import MemoryKind, MemoryRef, MemoryState
from tiangong_kernel.l0_primitives.serialization import stable_hash


def rid(prefix: str = "ref") -> RefId:
    return RefId(f"{prefix}:" + "7" * 32)


def test_phase5_objects_have_stable_hashes():
    objects = (
        MemoryRef(rid(), MemoryKind.USER, MemoryState.ACTIVE),
        ForgettingRef(rid(), ForgettingKind.PRUNING, ForgettingState.PRUNED),
        ContextRef(rid(), ContextKind.TASK_CONTEXT),
        LearningRef(rid(), LearningKind.SEMANTIC_LEARNING, LearningState.COMMITTED),
        HealthRef(rid(), HealthState.DEGRADED),
    )
    for obj in objects:
        assert stable_hash(obj) == stable_hash(obj)
        assert len(stable_hash(obj)) == 64
