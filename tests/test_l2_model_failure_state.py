from tiangong_kernel.l2_state.model_interaction_state import ModelFailureState


def test_l2_failure_state_normalizes_provider_error_fact():
    failure = ModelFailureState(provider_id="deepseek_v4", error_code="429", error_class="rate_limit", retryable=True)
    assert failure.retryable is True
