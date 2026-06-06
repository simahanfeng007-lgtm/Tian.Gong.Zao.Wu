from tiangong_kernel.l2_state.model_interaction_state import ModelInteractionState, ModelInvocationState, ModelProviderState


def test_l2_model_interaction_state_serializable():
    state = ModelInteractionState(
        interaction_state_id="interaction-ref:1",
        invocation_states=(ModelInvocationState(invocation_state_id="invocation-ref:1", provider_state=ModelProviderState(provider_id="mimo", model_id="mimo-v2.5-pro")),),
    )
    assert state.to_dict()["state_is_fact_only"] is True
