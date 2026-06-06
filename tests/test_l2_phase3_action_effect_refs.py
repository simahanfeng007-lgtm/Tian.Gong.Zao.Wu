from tiangong_kernel.l2_state import ActionIntentSource, ActionIntentStatus, EffectObservationStatus
from tests.test_l2_phase3_serialization import build_phase3_chain


def test_l2_phase3_action_effect_states_link_intent_to_observation_refs():
    chain = build_phase3_chain()
    action = chain["action_intent"]
    effect = chain["effect_observation"]
    boundary = chain["tool_boundary"]
    intent = chain["tool_intent"]

    assert action.action_source == ActionIntentSource.MODEL_TOOL_INTENT
    assert action.action_status == ActionIntentStatus.READY_FOR_UPPER_LAYER
    assert action.tool_intent_ref == intent.identity.state_ref
    assert action.boundary_state_ref == boundary.identity.state_ref
    assert effect.action_intent_ref == action.identity.state_ref
    assert effect.observation_status == EffectObservationStatus.OBSERVATION_PENDING
    assert effect.observation_refs
    assert effect.effect_refs
    assert effect.evidence_refs
