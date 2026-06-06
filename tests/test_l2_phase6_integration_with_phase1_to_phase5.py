from tiangong_kernel.l0_primitives.serialization import stable_hash, stable_json_dumps
from tiangong_kernel.l0_primitives.state import StateSnapshotRef
from tiangong_kernel.l2_state import (
    ContextSegmentKind,
    ContextSegmentState,
    ContextWindowState,
    L2SnapshotSummary,
    L2StateKind,
    L2StateSnapshot,
    LearningSignalKind,
    LearningSignalState,
    MemoryLayer,
    MemoryRefState,
    MemoryVisibilityStatus,
    RetrievalChannelKind,
    RetrievalResultRefState,
)
from tests.test_l2_phase5_cross_phase_references import build_phase5_chain
from tests.test_l2_phase6_memory_context_retrieval_learning_state import identity, ref, status, typed


def test_l2_phase6_states_link_to_phase1_to_phase5_refs_without_execution_objects():
    phase5 = build_phase5_chain()
    phase4 = phase5["phase4"]
    phase3 = phase4["phase3"]
    run_ref = phase3["run"].identity.state_ref
    task_ref = phase3["task"].identity.state_ref
    skill_ref = phase3["skill_activation"].identity.state_ref
    boundary_ref = phase4["boundary_check"].identity.state_ref
    observation_frame_ref = phase5["frame"].identity.state_ref

    memory = MemoryRefState(
        identity=identity(600),
        status=status(),
        memory_ref_id=typed(601, "memory"),
        layer=MemoryLayer.EPISODIC,
        source_ref=observation_frame_ref,
        content_hash="sha256:cross-phase-memory",
        summary="observation-backed memory reference",
        visibility=MemoryVisibilityStatus.REFERENCED,
        confidence=0.7,
        related_run_ref=run_ref,
        related_task_ref=task_ref,
        related_skill_ref=skill_ref,
    )
    segment = ContextSegmentState(
        identity=identity(610),
        status=status(),
        segment_id=typed(611, "context_segment"),
        kind=ContextSegmentKind.SKILL_REF,
        source_ref=skill_ref,
        token_estimate=64,
        related_run_ref=run_ref,
        related_task_ref=task_ref,
        related_skill_ref=skill_ref,
    )
    window = ContextWindowState(
        identity=identity(620),
        status=status(),
        window_id=typed(621, "context_window"),
        active_segments=(segment.identity.state_ref,),
        model_request_ref=phase3["model_request"].identity.state_ref,
    )
    retrieval_result = RetrievalResultRefState(
        identity=identity(630),
        status=status(),
        result_ref_id=typed(631, "retrieval_result"),
        source_ref=observation_frame_ref,
        channel_kind=RetrievalChannelKind.OBSERVATION_STREAM,
        rank=1,
        score=0.8,
        summary="observation frame as retrieval result ref",
    )
    signal = LearningSignalState(
        identity=identity(640),
        status=status(),
        signal_id=typed(641, "learning_signal"),
        kind=LearningSignalKind.OBSERVATION_GAP,
        source_ref=phase5["quality"].identity.state_ref,
        strength=0.5,
        urgency=0.3,
        related_observation_refs=(observation_frame_ref,),
    )
    snapshot = L2StateSnapshot(
        snapshot_ref=StateSnapshotRef(ref("snap", 1)),
        state_refs=(
            memory.identity.state_ref,
            segment.identity.state_ref,
            window.identity.state_ref,
            retrieval_result.identity.state_ref,
            signal.identity.state_ref,
        ),
        summary=L2SnapshotSummary(total_states=5, active_states=1, blocked_states=0, failed_states=0),
    )

    assert memory.source_ref == observation_frame_ref
    assert memory.related_run_ref == run_ref
    assert segment.source_ref == skill_ref
    assert window.model_request_ref == phase3["model_request"].identity.state_ref
    assert retrieval_result.source_ref == observation_frame_ref
    assert signal.related_observation_refs == (observation_frame_ref,)
    assert boundary_ref.ref_type == "boundary"
    assert stable_json_dumps(snapshot)
    assert len(stable_hash(snapshot)) == 64


def test_l2_phase6_public_init_exports_new_objects_without_side_effects():
    import tiangong_kernel.l2_state as l2_state

    exported = set(l2_state.__all__)
    required = {
        "MemoryRefState",
        "ContextWindowState",
        "RetrievalRequestState",
        "LearningSignalState",
        "KnowledgeReferenceState",
    }
    assert required.issubset(exported)
    assert l2_state.L2StateKind.MEMORY_CONTEXT is L2StateKind.MEMORY_CONTEXT
