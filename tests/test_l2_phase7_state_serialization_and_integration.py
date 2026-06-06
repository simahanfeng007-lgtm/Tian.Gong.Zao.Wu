from tiangong_kernel.l0_primitives.serialization import stable_hash, stable_json_dumps
from tiangong_kernel.l2_state import (
    CandidateKind,
    CandidateRefState,
    ContextWindowState,
    ExperimentIntentState,
    ExperimentKind,
    IterationCandidateState,
    IterationTargetKind,
    L2SnapshotSummary,
    L2StateIdentity,
    L2StateKind,
    L2StateSnapshot,
    L2StateStatus,
    L2StateStatusKind,
    LearningSignalState,
    LearningSignalKind,
    MemoryRefState,
    RetrievalResultRefState,
)
from tiangong_kernel.l0_primitives.identity import RefId, TypedRef
from tiangong_kernel.l0_primitives.state import StateSnapshotRef


def ref(prefix: str, index: int) -> RefId:
    return RefId(f"{prefix}:{index:032x}")


def typed(index: int, ref_type: str) -> TypedRef:
    return TypedRef(ref("phase7", index), ref_type)


def identity(index: int, kind: L2StateKind) -> L2StateIdentity:
    return L2StateIdentity(state_ref=typed(index, kind.value), kind=kind)


def status() -> L2StateStatus:
    return L2StateStatus(kind=L2StateStatusKind.DECLARED, reason="phase7 fixture")


def test_l2_phase7_objects_are_stably_serializable_and_hashable():
    candidate = CandidateRefState(
        identity=identity(1, L2StateKind.CANDIDATE),
        status=status(),
        candidate_ref=typed(2, "candidate"),
        candidate_kind=CandidateKind.LEARNING,
        summary="candidate serialization fixture",
        priority=0.5,
    )
    iteration = IterationCandidateState(
        identity=identity(3, L2StateKind.CANDIDATE),
        status=status(),
        iteration_candidate_ref=typed(4, "iteration_candidate"),
        candidate_ref=candidate.identity.state_ref,
        target_kind=IterationTargetKind.SKILL_FLOW,
        target_ref=typed(5, "skill"),
    )
    experiment = ExperimentIntentState(
        identity=identity(6, L2StateKind.EXPERIMENT),
        status=status(),
        experiment_intent_ref=typed(7, "experiment_intent"),
        candidate_ref=candidate.identity.state_ref,
        experiment_kind=ExperimentKind.SKILL_FLOW,
    )
    for item in (candidate, iteration, experiment):
        payload = stable_json_dumps(item)
        digest = stable_hash(item)
        assert isinstance(payload, str)
        assert isinstance(digest, str)
        assert len(digest) == 64
        assert stable_hash(item) == digest


def test_l2_phase7_candidate_can_reference_phase6_learning_memory_context_and_retrieval_states():
    memory = MemoryRefState(identity=identity(10, L2StateKind.MEMORY_CONTEXT), status=status(), memory_ref_id=typed(11, "memory"))
    context = ContextWindowState(identity=identity(12, L2StateKind.MEMORY_CONTEXT), status=status(), window_id=typed(13, "context_window"))
    retrieval = RetrievalResultRefState(identity=identity(14, L2StateKind.MEMORY_CONTEXT), status=status(), result_ref_id=typed(15, "retrieval_result"))
    learning = LearningSignalState(
        identity=identity(16, L2StateKind.MEMORY_CONTEXT),
        status=status(),
        signal_id=typed(17, "learning_signal"),
        kind=LearningSignalKind.MODEL_REFLECTION,
    )
    candidate = CandidateRefState(
        identity=identity(18, L2StateKind.CANDIDATE),
        status=status(),
        candidate_ref=typed(19, "candidate"),
        source_ref=learning.identity.state_ref,
        subject_ref=memory.identity.state_ref,
        summary="candidate can point to phase6 memory context retrieval learning refs",
    )
    snapshot = L2StateSnapshot(
        snapshot_ref=StateSnapshotRef(ref("snapshot", 1)),
        state_refs=(
            memory.identity.state_ref,
            context.identity.state_ref,
            retrieval.identity.state_ref,
            learning.identity.state_ref,
            candidate.identity.state_ref,
        ),
        summary=L2SnapshotSummary(total_states=5, active_states=5),
    )
    assert candidate.source_ref == learning.identity.state_ref
    assert len(snapshot.state_refs) == 5
    assert stable_hash(snapshot)


def test_l2_phase7_stable_hash_changes_when_candidate_fact_changes():
    first = CandidateRefState(identity=identity(20, L2StateKind.CANDIDATE), status=status(), summary="first", priority=0.2)
    second = CandidateRefState(identity=first.identity, status=first.status, summary="second", priority=0.2)
    assert stable_hash(first) != stable_hash(second)
