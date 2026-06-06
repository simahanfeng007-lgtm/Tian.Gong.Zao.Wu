from tests.test_l2_phase3_serialization import build_phase3_chain


def test_l2_phase3_full_main_chain_is_pure_reference_composition():
    chain = build_phase3_chain()

    assert chain["task"].run_ref == chain["run"].identity.state_ref
    assert chain["skill_selection"].source_message_ref is not None
    assert chain["skill_activation"].selection_state_ref == chain["skill_selection"].identity.state_ref
    assert chain["tool_declaration"].skill_activation_ref == chain["skill_activation"].identity.state_ref
    assert chain["tool_visibility"].declaration_state_ref == chain["tool_declaration"].identity.state_ref
    assert chain["tool_release"].visibility_state_ref == chain["tool_visibility"].identity.state_ref
    assert chain["tool_lease"].release_state_ref == chain["tool_release"].identity.state_ref
    assert chain["model_response"].request_state_ref == chain["model_request"].identity.state_ref
    assert chain["tool_intent"].model_response_ref == chain["model_response"].identity.state_ref
    assert chain["tool_boundary"].tool_intent_ref == chain["tool_intent"].identity.state_ref
    assert chain["action_intent"].tool_intent_ref == chain["tool_intent"].identity.state_ref
    assert chain["effect_observation"].action_intent_ref == chain["action_intent"].identity.state_ref
    assert chain["feedback"].response_state_ref == chain["model_response"].identity.state_ref
    assert chain["reflection"].feedback_state_ref == chain["feedback"].identity.state_ref
