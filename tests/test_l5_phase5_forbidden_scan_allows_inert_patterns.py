from tiangong_kernel.l5_plugin_host import public_text_is_safe


def test_inert_pattern_catalog_strings_can_be_discussed_in_tests():
    inert = ("importlib.import_module", "subprocess", "Path.write_text", "sandbox_requirement_ref")
    assert "importlib.import_module" in inert
    assert public_text_is_safe(("sandbox_requirement_ref", "credential_policy_ref"))
