from l3_phase6_builders import build_l3_phase6_objects
from tiangong_kernel.l3_orchestration import SubsystemServiceKind, SubsystemServiceRequestStatus


def test_subsystem_service_request_is_pure_request_object():
    objects = build_l3_phase6_objects()
    request = objects["subsystem_request"]
    envelope = objects["subsystem_envelope"]
    transition = objects["subsystem_transition"]
    assert request.request_only is True
    assert request.request_ref.service_kind is SubsystemServiceKind.MEMORY
    assert envelope.status is SubsystemServiceRequestStatus.READY_FOR_FUTURE_SERVICE
    assert envelope.request_only is True
    assert transition.advisory_only is True
    assert not hasattr(request, "service_client")
    assert not hasattr(request, "plugin_host")


def test_memory_retrieval_learning_affective_requests_are_not_real_services():
    objects = build_l3_phase6_objects()
    memory = objects["memory_request"]
    retrieval = objects["retrieval_request"]
    learning = objects["learning_request"]
    affective = objects["affective_request"]
    assert memory.request_only is True
    assert retrieval.request_only is True
    assert learning.request_only is True
    assert affective.request_only is True
    assert objects["write_suggestion"].suggestion_only is True
    assert objects["query_hint"].advisory_only is True
    assert objects["learning_signal"].advisory_only is True
    assert objects["tendency"].advisory_only is True
    assert not hasattr(memory, "memory_store")
    assert not hasattr(retrieval, "search")
    assert not hasattr(learning, "skill_generator")
    assert not hasattr(affective, "emotion_engine")
