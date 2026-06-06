from tiangong_kernel.l4_action_grounding.model_provider_adapter import (
    MiMoOrdinaryApiRequestMapper,
    MiMoRequestMapper,
    MiMoTokenPlanRequestMapper,
    all_provider_factsheets,
    mimo_api_surface_descriptors,
)


class _Dispatch:
    dispatch_request_ref = "dispatch-ref:test"


def test_mimo_model_ids_are_lowercase():
    factsheet = all_provider_factsheets()["mimo"]
    assert factsheet.default_model_id == factsheet.default_model_id.lower()
    assert all(model_id == model_id.lower() for model_id in factsheet.supported_model_ids)
    assert "mimo-v2-flash" in factsheet.supported_model_ids


def test_mimo_supports_token_plan_and_ordinary_api_surfaces_ref_only():
    descriptors = mimo_api_surface_descriptors()
    assert set(descriptors) == {"token_plan_api", "ordinary_api"}
    assert descriptors["token_plan_api"].endpoint_is_ref_only is True
    assert descriptors["ordinary_api"].credential_is_handle_only is True
    assert descriptors["ordinary_api"].selected_by_l5_scope is True

    ordinary = MiMoOrdinaryApiRequestMapper().map_request(_Dispatch())
    plan = MiMoTokenPlanRequestMapper().map_request(_Dispatch())
    explicit = MiMoRequestMapper().map_request(_Dispatch(), api_surface="token_plan_api")
    assert ordinary["api_surface"] == "ordinary_api"
    assert plan["api_surface"] == "token_plan_api"
    assert explicit["api_surface"] == "token_plan_api"
    assert ordinary["provider_specific_http_not_sent"] is True
    assert plan["supports_token_plan_and_ordinary_api"] is True
