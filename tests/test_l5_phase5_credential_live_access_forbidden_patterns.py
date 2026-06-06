from tiangong_kernel.l5_plugin_host import has_live_locator


def test_live_credential_access_patterns_are_flagged_as_locators():
    assert has_live_locator("file:///secrets/token")
    assert has_live_locator("https://vault.example.invalid/token")
