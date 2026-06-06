from l5_phase5_helpers import validate_all, valid_credential


def test_credential_handle_refs_cannot_be_real_locator():
    report = validate_all(credential_decls=(valid_credential(credential_handle_refs=("/secret/path",)),))
    assert report.p0_count >= 1
