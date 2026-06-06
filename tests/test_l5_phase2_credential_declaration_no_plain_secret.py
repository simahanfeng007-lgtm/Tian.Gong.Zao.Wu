import pytest

from tiangong_kernel.l5_plugin_host import PluginCredentialDeclaration


def test_credential_declaration_allows_safe_field_names_but_not_values():
    decl = PluginCredentialDeclaration(
        credential_handle_refs=("credential_handle:declared",),
        secret_scope_refs=("secret_scope:declared",),
        credential_purpose_refs=("purpose:declared",),
        credential_revocation_ref="revocation:declared",
        credential_lease_ref="lease:declared",
    )
    assert decl.value_absent_required
    with pytest.raises(ValueError):
        PluginCredentialDeclaration(
            credential_handle_refs=("s" "k-1234567890abcdef",),
            credential_purpose_refs=("purpose:declared",),
            credential_revocation_ref="revocation:declared",
            credential_lease_ref="lease:declared",
        )
