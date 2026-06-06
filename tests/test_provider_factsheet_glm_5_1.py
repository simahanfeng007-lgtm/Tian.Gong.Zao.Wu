from tiangong_kernel.l4_action_grounding.model_provider_adapter import all_provider_factsheets


def test_factsheet_required_fields():
    provider_id, model_id = ("glm_5_1", "glm-5.1")
    factsheet = all_provider_factsheets()[provider_id]
    assert factsheet.provider_id == provider_id
    assert model_id in factsheet.supported_model_ids or model_id == factsheet.default_model_id
    assert factsheet.credential_handle_required is True
    assert factsheet.official_doc_url_ref
    assert factsheet.verified_at == "2026-06-05"
    assert factsheet.unknown_or_unverified_fields
