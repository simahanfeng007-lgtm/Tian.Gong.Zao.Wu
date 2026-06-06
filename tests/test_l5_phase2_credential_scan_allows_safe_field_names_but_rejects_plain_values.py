from tiangong_kernel.l5_plugin_host.phase2_common import suspicious_credential_value_paths


def test_safe_credential_field_names_are_not_plain_secret_values():
    safe = {
        "credential_secret_refs": ["credential_secret:declared"],
        "secret_scope_refs": ["secret_scope:declared"],
        "token_scope_refs": ["token_scope:declared"],
    }
    assert suspicious_credential_value_paths(safe) == ()


def test_plain_assignment_values_are_rejected():
    for key in ("pass" "word=", "api" "_key=", "to" "ken=", "se" "cret="):
        assert suspicious_credential_value_paths({"value": key + "realvalue123"})
