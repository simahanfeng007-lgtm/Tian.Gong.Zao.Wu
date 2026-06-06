from tiangong_kernel.l2_state.model_interaction_state import ModelFallbackState


def test_l2_fallback_state_does_not_execute():
    fb = ModelFallbackState(attempted=True, from_provider_id="gpt_5_5", to_provider_id="glm_5_1", executed_by_l4_with_l5_permit=False)
    assert fb.attempted is True
    assert fb.executed_by_l4_with_l5_permit is False
