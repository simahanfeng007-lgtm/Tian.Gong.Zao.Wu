from tiangong_kernel.l5_plugin_host.phase2_common import suspicious_credential_value_paths


def test_credential_scan_allows_governance_field_names():
    value = {
        "secret_scope_refs": ["secret_scope:declared"],
        "credential_handle_refs": ["credential_handle:declared"],
        "redaction_required": True,
    }
    assert suspicious_credential_value_paths(value) == ()


def test_credential_scan_rejects_suspected_plain_values():
    value = {"credential_handle_refs": ["s" "k-1234567890abcdef"]}
    assert suspicious_credential_value_paths(value)
