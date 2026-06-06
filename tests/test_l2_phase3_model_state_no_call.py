from tiangong_kernel.l2_state import ModelFeedbackKind, ModelReflectionStatus, ModelRequestStatus, ModelResponseStatus
from tests.test_l2_phase3_serialization import build_phase3_chain


def test_l2_phase3_model_states_record_refs_without_calling_model():
    chain = build_phase3_chain()
    request = chain["model_request"]
    response = chain["model_response"]
    feedback = chain["feedback"]
    reflection = chain["reflection"]
    tool_intent = chain["tool_intent"]

    assert request.request_status == ModelRequestStatus.VISIBLE_CONTEXT_BUILT
    assert request.visible_skill_refs
    assert request.visible_tool_group_refs
    assert response.response_status == ModelResponseStatus.TOOL_INTENT_FOUND
    assert tool_intent.model_response_ref == response.identity.state_ref
    assert feedback.feedback_kind == ModelFeedbackKind.TASK_PROGRESS
    assert feedback.response_state_ref == response.identity.state_ref
    assert reflection.reflection_status == ModelReflectionStatus.RECORDED
    assert reflection.feedback_state_ref == feedback.identity.state_ref
