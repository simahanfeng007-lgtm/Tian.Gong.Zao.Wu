from tiangong_kernel.l5_plugin_host import public_text_is_safe


def test_governance_field_names_are_not_secret_values():
    assert public_text_is_safe(("credential_handle_refs", "secret redaction", "token_budget_ref", "capability_token_boundary_decl_ref"))
