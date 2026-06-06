from tiangong_kernel.l4_action_grounding.model_provider_adapter import all_provider_factsheets


def test_unknown_fields_are_explicit():
    for factsheet in all_provider_factsheets().values():
        assert factsheet.unknown_or_unverified_fields
        assert all(isinstance(item, str) and item for item in factsheet.unknown_or_unverified_fields)
