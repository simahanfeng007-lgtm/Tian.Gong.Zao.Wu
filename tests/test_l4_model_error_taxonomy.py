from tiangong_kernel.l4_action_grounding.model_provider_adapter import MiniMaxM3ErrorMapper, provider_error_taxonomy_matrix


def test_l4_error_mapper_normalizes_failure():
    failure = MiniMaxM3ErrorMapper().map_error("429", retryable=True)
    assert failure.retryable is True
    assert "minimax_m3" in provider_error_taxonomy_matrix()
