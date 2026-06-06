from l4_phase8_builders import final_freeze_readiness, l5_handoff, l6_execution_service_need
from tiangong_kernel.l4_action_grounding import action_grounding_stable_hash, action_grounding_to_primitive


def test_l4_phase8_objects_are_stably_serializable():
    handoff = l5_handoff()
    need = l6_execution_service_need()
    readiness = final_freeze_readiness()

    handoff_primitive = action_grounding_to_primitive(handoff)
    need_primitive = action_grounding_to_primitive(need)
    digest = action_grounding_stable_hash(readiness)

    assert handoff_primitive["envelope_only"] is True
    assert need_primitive["implements_service"] is False
    assert len(digest) >= 32
