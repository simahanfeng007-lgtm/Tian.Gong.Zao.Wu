from tiangong_kernel.l5_plugin_host.phase2_common import suspicious_credential_value_paths


def test_static_scan_distinguishes_security_field_names_from_plain_values():
    safe = {
        "api_key_policy_ref": "policy:api_key",
        "password_policy_ref": "policy:password",
        "no_plain_secret": True,
        "token_scope_refs": ["scope:token"],
    }
    unsafe = {"header": "Bear" "er abcdefghijklmnopqrstuvwxyz"}
    assert suspicious_credential_value_paths(safe) == ()
    assert suspicious_credential_value_paths(unsafe)
