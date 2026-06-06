from tiangong_kernel.l4_action_grounding.model_provider_adapter import all_provider_factsheets


def test_factsheet_required_fields():
    provider_id, model_id = ("gpt_5_5", "gpt-5.5")
    factsheet = all_provider_factsheets()[provider_id]
    assert factsheet.provider_id == provider_id
    assert model_id in factsheet.supported_model_ids or model_id == factsheet.default_model_id
    assert factsheet.credential_handle_required is True
    assert factsheet.official_doc_url_ref
    assert factsheet.verified_at == "2026-06-05"
    assert factsheet.unknown_or_unverified_fields


def test_gpt55_uses_precise_developer_docs_and_current_window():
    factsheet = all_provider_factsheets()["gpt_5_5"]
    assert "developers.openai.com/api/docs/models/gpt-5.5" in factsheet.official_doc_url_ref
    assert "developers.openai.com/api/docs/guides/latest-model" in factsheet.official_doc_url_ref
    assert factsheet.context_window_tokens == 1_050_000
    assert factsheet.max_output_tokens == 128_000
