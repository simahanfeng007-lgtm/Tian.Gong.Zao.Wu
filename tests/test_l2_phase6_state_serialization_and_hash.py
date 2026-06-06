from tiangong_kernel.l0_primitives.serialization import stable_hash, stable_json_dumps
from tests.test_l2_phase6_memory_context_retrieval_learning_state import build_phase6_objects


def test_l2_phase6_objects_are_stably_serializable_and_hashable():
    for name, item in build_phase6_objects().items():
        payload = stable_json_dumps(item)
        digest = stable_hash(item)
        assert isinstance(payload, str), name
        assert isinstance(digest, str), name
        assert len(digest) == 64, name
        assert stable_hash(item) == digest, name


def test_l2_phase6_stable_hash_changes_when_state_fact_changes():
    objects = build_phase6_objects()
    memory = objects["memory"]
    changed = type(memory)(
        identity=memory.identity,
        status=memory.status,
        memory_ref_id=memory.memory_ref_id,
        layer=memory.layer,
        scope_ref=memory.scope_ref,
        source_ref=memory.source_ref,
        content_hash="sha256:changed",
        summary=memory.summary,
        visibility=memory.visibility,
        confidence=memory.confidence,
        freshness=memory.freshness,
        boundary_status=memory.boundary_status,
        created_at_ref=memory.created_at_ref,
        updated_at_ref=memory.updated_at_ref,
        related_run_ref=memory.related_run_ref,
        related_task_ref=memory.related_task_ref,
        related_skill_ref=memory.related_skill_ref,
        metadata=memory.metadata,
        schema_version=memory.schema_version,
    )
    assert stable_hash(memory) != stable_hash(changed)
