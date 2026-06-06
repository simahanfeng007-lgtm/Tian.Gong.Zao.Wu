from l3_phase2_builders import build_l3_phase2_objects
from tiangong_kernel.l2_state import L2StateStatusKind
from tiangong_kernel.l3_orchestration import (
    OrchestrationLifecycleKind,
    l2_status_hint_for_lifecycle,
)


def test_l3_phase2_lifecycle_enum_contains_required_states():
    required = {
        "created",
        "prepared",
        "active",
        "waiting",
        "paused",
        "blocked",
        "failed",
        "cancelled",
        "completed",
        "resumable",
        "abandoned",
    }
    assert required.issubset({item.value for item in OrchestrationLifecycleKind})


def test_l3_phase2_transition_advice_is_advisory_and_maps_to_l2_status_hint():
    objects = build_l3_phase2_objects()
    process_advice = objects["process_advice"]
    assert process_advice.advisory_only is True
    assert process_advice.suggested_lifecycle is OrchestrationLifecycleKind.RESUMABLE
    assert process_advice.l2_state_update_suggestions[0].advisory_only is True
    assert process_advice.l2_state_update_suggestions[0].suggested_status is L2StateStatusKind.WAITING
    assert l2_status_hint_for_lifecycle(OrchestrationLifecycleKind.CANCELLED) is L2StateStatusKind.REVOKED
    assert l2_status_hint_for_lifecycle(OrchestrationLifecycleKind.ABANDONED) is L2StateStatusKind.SUPERSEDED
