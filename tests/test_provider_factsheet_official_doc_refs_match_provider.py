from tiangong_kernel.l4_action_grounding.model_provider_adapter import all_provider_factsheets


def test_official_doc_refs_match_provider_and_model():
    refs = {pid: fs.official_doc_url_ref for pid, fs in all_provider_factsheets().items()}
    assert "news260424" in refs["deepseek_v4"]
    assert "news251201" not in refs["deepseek_v4"]
    assert "mimo.mi.com" in refs["mimo"]
    assert "xiaomimimo.com/docs/en-US/quick-start/model" in refs["mimo"]
    assert "xiaomimimo.com/docs/en-US/updates/model" in refs["mimo"]
    assert "xiaomimimo.com/docs/en-US/price/pay-as-you-go" in refs["mimo"]
    assert "xiaomimimo.com/docs/en-US/price/tokenplan/quick-access" in refs["mimo"]
    assert "xiaomimimo.com/docs/en-US/quick-start/error-codes" in refs["mimo"]
    assert "xiaomimimo.com/docs/en-US/quick-start/model-hyperparameters" in refs["mimo"]
    assert "docs.z.ai" in refs["glm_5_1"] and "glm-5.1" in refs["glm_5_1"]
    assert "platform.minimax.io" in refs["minimax_m3"] and "models-intro" in refs["minimax_m3"]
    assert "developers.openai.com/api/docs/models/gpt-5.5" in refs["gpt_5_5"]
    assert "developers.openai.com/api/docs/guides/latest-model" in refs["gpt_5_5"]
