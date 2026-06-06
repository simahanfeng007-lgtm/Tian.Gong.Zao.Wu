from tiangong_kernel.l2_state.model_interaction_state import ModelTokenUsageState, ModelLatencyState


def test_l2_usage_and_latency_are_facts():
    usage = ModelTokenUsageState(prompt_tokens=10, completion_tokens=5, total_tokens=15)
    latency = ModelLatencyState(first_token_ms=100, total_latency_ms=250)
    assert usage.total_tokens == 15
    assert latency.total_latency_ms == 250
