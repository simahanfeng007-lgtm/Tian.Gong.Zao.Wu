from tiangong_kernel.l5_plugin_host.phase2_common import suspicious_credential_value_paths


def test_secret_like_values_are_detected():
    hits = suspicious_credential_value_paths({"value": "sk-123456789012345"})
    assert hits
