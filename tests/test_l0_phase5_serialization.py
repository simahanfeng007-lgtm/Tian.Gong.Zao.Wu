from tiangong_kernel.l0_primitives.context import ContextKind, ContextRef
from tiangong_kernel.l0_primitives.forgetting import ForgettingKind, ForgettingRef, ForgettingState
from tiangong_kernel.l0_primitives.health import HealthRef, HealthState
from tiangong_kernel.l0_primitives.identity import RefId
from tiangong_kernel.l0_primitives.learning import LearningKind, LearningRef, LearningState
from tiangong_kernel.l0_primitives.memory import MemoryKind, MemoryRef, MemoryState
from tiangong_kernel.l0_primitives.serialization import stable_json_dumps


def rid(prefix: str = "ref") -> RefId:
    return RefId(f"{prefix}:" + "6" * 32)


def test_phase5_objects_have_stable_json():
    objects = (
        MemoryRef(rid(), MemoryKind.SELF, MemoryState.STABLE),
        ForgettingRef(rid(), ForgettingKind.SUPPRESSION, ForgettingState.SUPPRESSED),
        ContextRef(rid(), ContextKind.RUN_CONTEXT),
        LearningRef(rid(), LearningKind.FEEDBACK_LEARNING, LearningState.ACTIVE),
        HealthRef(rid(), HealthState.WATCH),
    )
    for obj in objects:
        first = stable_json_dumps(obj)
        second = stable_json_dumps(obj)
        assert first == second
        assert "schema_version" in first
