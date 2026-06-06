from tiangong_kernel.l4_action_grounding.model_provider_adapter import provider_capability_matrix, provider_endpoint_matrix, provider_feature_gap_matrix, provider_risk_surface_matrix, provider_budget_matrix, provider_error_taxonomy_matrix


def test_provider_matrices_cover_five_providers():
    expected = {"deepseek_v4", "mimo", "glm_5_1", "minimax_m3", "gpt_5_5"}
    for matrix in (provider_capability_matrix(), provider_endpoint_matrix(), provider_feature_gap_matrix(), provider_risk_surface_matrix(), provider_budget_matrix(), provider_error_taxonomy_matrix()):
        assert set(matrix) == expected
