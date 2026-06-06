from tiangong_kernel.l0_primitives.identity import TypedRef
from tests.test_l2_phase4_serialization import build_phase4_objects


def test_l2_phase4_boundary_risk_resource_security_and_control_link_phase3_refs():
    objects = build_phase4_objects()
    phase3 = objects["phase3"]

    assert objects["boundary_check"].checked_subject_ref == phase3["tool_intent"].identity.state_ref
    assert objects["risk"].subject_ref == phase3["action_intent"].identity.state_ref
    assert objects["lease"].tool_group_release_state_ref == phase3["tool_release"].identity.state_ref
    assert objects["security"].subject_ref == phase3["effect_observation"].identity.state_ref
    assert objects["control"].model_feedback_state_ref == phase3["feedback"].identity.state_ref
    assert objects["control"].tool_intent_state_ref == phase3["tool_intent"].identity.state_ref


def test_l2_phase4_integration_chain_uses_typed_refs_not_embedded_executors():
    objects = build_phase4_objects()
    checked_refs = (
        objects["boundary_check"].checked_subject_ref,
        objects["risk"].subject_ref,
        objects["lease"].tool_group_release_state_ref,
        objects["security"].subject_ref,
        objects["control"].tool_intent_state_ref,
    )

    assert all(isinstance(item, TypedRef) for item in checked_refs)
    assert not hasattr(objects["control"], "tool")
    assert not hasattr(objects["boundary_check"], "executor")
