from tiangong_kernel.l4_action_grounding.model_provider_adapter import GPT55StreamMapper


def test_l4_stream_mapper_normalizes_fake_event():
    event = GPT55StreamMapper().map_event("stream-ref:1", 1)
    assert event.normalized_only is True
    assert event.sequence == 1
