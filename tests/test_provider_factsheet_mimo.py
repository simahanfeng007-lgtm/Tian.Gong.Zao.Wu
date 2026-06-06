from tiangong_kernel.l4_action_grounding.model_provider_adapter import all_provider_factsheets


def test_factsheet_required_fields():
    provider_id, model_id = ("mimo", "mimo-v2.5-pro")
    factsheet = all_provider_factsheets()[provider_id]
    assert factsheet.provider_id == provider_id
    assert model_id in factsheet.supported_model_ids or model_id == factsheet.default_model_id
    assert factsheet.credential_handle_required is True
    assert factsheet.official_doc_url_ref
    assert factsheet.verified_at == "2026-06-05"
    assert factsheet.unknown_or_unverified_fields


def test_mimo_factsheet_uses_granular_official_refs_and_verified_limits():
    factsheet = all_provider_factsheets()["mimo"]
    refs = factsheet.official_doc_url_ref
    for required in (
        "quick-start/model",
        "updates/model",
        "price/pay-as-you-go",
        "price/tokenplan/quick-access",
        "quick-start/error-codes",
        "quick-start/model-hyperparameters",
    ):
        assert required in refs
    assert factsheet.streaming_supported is True
    assert factsheet.max_output_tokens == 128_000
    assert factsheet.cache_supported is True
    assert "400/401/402/403/404/421/429/500/503" in factsheet.error_code_shape
    assert "error_code_shape" not in factsheet.unknown_or_unverified_fields
