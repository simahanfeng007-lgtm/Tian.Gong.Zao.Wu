from l5_phase5_helpers import valid_credential


def test_credential_declaration_keeps_values_absent_and_redacted():
    decl = valid_credential()
    assert decl.value_absent_required is True
    assert decl.redacted_required is True
    assert not hasattr(decl, "raw_value")
    assert not hasattr(decl, "token_value")
    assert not hasattr(decl, "password_value")
