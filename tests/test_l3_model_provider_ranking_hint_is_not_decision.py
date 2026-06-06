import pytest
from tiangong_kernel.l3_orchestration.model_invocation_flow import ModelProviderRankingHint


def test_l3_provider_ranking_hint_is_not_decision():
    hint = ModelProviderRankingHint(ranking_hint_ref="rank-ref:1", ranked_provider_ids=("minimax_m3", "gpt_5_5"))
    assert hint.advisory_only is True
    with pytest.raises(ValueError):
        ModelProviderRankingHint(ranking_hint_ref="rank-ref:2", ranked_provider_ids=("gpt_5_5",), provider_selection_decision=True)
